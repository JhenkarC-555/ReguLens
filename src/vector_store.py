"""
src/vector_store.py - ReguLens Vector Index & Semantic Retrieval Module
Generates dense embeddings with Sentence Transformers and indexes them with FAISS.
Provides exact mapping to source chunks, persistence, threshold filtering,
and a deterministic fallback retriever if the neural model is offline.
"""

from __future__ import annotations
import json
import logging
import math
import os
import pickle
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from src.text_processor import TextChunk

logger = logging.getLogger(__name__)

# Try importing FAISS and SentenceTransformers
try:
    import faiss
    HAS_FAISS = True
except ImportError:
    faiss = None
    HAS_FAISS = False

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    SentenceTransformer = None
    HAS_SENTENCE_TRANSFORMERS = False


class FallbackLexicalRetriever:
    """
    Lightweight, dependency-free TF-IDF retriever used when FAISS or
    SentenceTransformer models are missing or downloading is disabled.
    Guarantees that retrieval and search workflows never crash.
    """

    def __init__(self):
        self.chunks: List[TextChunk] = []
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.tfidf_matrix: Optional[np.ndarray] = None

    def fit(self, chunks: List[TextChunk]):
        self.chunks = chunks
        if not chunks:
            self.tfidf_matrix = None
            return

        doc_tokens = [self._tokenize(c.text) for c in chunks]
        df: Dict[str, int] = {}
        all_words = set()

        for tokens in doc_tokens:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                df[t] = df.get(t, 0) + 1
                all_words.add(t)

        self.vocab = {w: i for i, w in enumerate(sorted(all_words))}
        num_docs = len(chunks)
        self.idf = {w: math.log((num_docs + 1) / (df[w] + 1)) + 1.0 for w in self.vocab}

        # Build matrix
        matrix = np.zeros((num_docs, len(self.vocab)), dtype=np.float32)
        for i, tokens in enumerate(doc_tokens):
            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            for t, count in tf.items():
                if t in self.vocab:
                    col = self.vocab[t]
                    matrix[i, col] = (count / max(len(tokens), 1)) * self.idf[t]

        # L2 normalize
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.tfidf_matrix = matrix / norms

    def search(self, query: str, top_k: int = 5) -> List[Tuple[TextChunk, float]]:
        if self.tfidf_matrix is None or not self.chunks:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        q_vec = np.zeros((1, len(self.vocab)), dtype=np.float32)
        tf: Dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1

        for t, count in tf.items():
            if t in self.vocab:
                col = self.vocab[t]
                q_vec[0, col] = (count / max(len(tokens), 1)) * self.idf.get(t, 1.0)

        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []
        q_vec = q_vec / q_norm

        scores = np.dot(self.tfidf_matrix, q_vec.T).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results: List[Tuple[TextChunk, float]] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score > 0.0:
                results.append((self.chunks[idx], score))
        return results

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9]{2,}\b", text.lower())


class VectorStore:
    """
    Production-grade Vector Index using SentenceTransformers and FAISS.
    Features:
    - Cosine similarity with normalized vectors
    - Source metadata mapping
    - On-disk index caching in data/processed/
    - Transparent fallback to lexical retriever if models fail to initialize
    """

    DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        processed_dir: Optional[str] = "data/processed",
        use_fallback_if_needed: bool = True,
    ):
        self.model_name = model_name
        self.processed_dir = Path(processed_dir) if processed_dir else Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.use_fallback_if_needed = use_fallback_if_needed

        self.model: Optional[Any] = None
        self.faiss_index: Optional[Any] = None
        self.chunks: List[TextChunk] = []
        self.embedding_dimension: int = 384
        self.is_neural_ready: bool = False
        self.fallback_retriever = FallbackLexicalRetriever()

        # Initialize embedding model lazily or immediately
        self._initialize_model()

    def _initialize_model(self) -> bool:
        """Attempts to load the SentenceTransformer model."""
        if not HAS_SENTENCE_TRANSFORMERS or not HAS_FAISS:
            self.is_neural_ready = False
            return False

        try:
            self.model = SentenceTransformer(self.model_name)
            if hasattr(self.model, "get_embedding_dimension"):
                self.embedding_dimension = self.model.get_embedding_dimension()
            else:
                self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            self.is_neural_ready = True
            return True
        except Exception as e:
            logger.warning(
                f"Could not load SentenceTransformer '{self.model_name}': {e}. "
                "Retaining fallback lexical search."
            )
            self.is_neural_ready = False
            return False

    def build_index(self, chunks: List[TextChunk]) -> bool:
        """
        Embeds chunks and creates a FAISS IndexFlatIP (Cosine Similarity) index.
        Also fits the fallback lexical retriever.
        """
        self.chunks = list(chunks)

        # Always fit fallback lexical retriever for hybrid / resilience
        self.fallback_retriever.fit(self.chunks)

        if not self.chunks:
            self.faiss_index = None
            return True

        if not self.is_neural_ready and not self._initialize_model():
            logger.info("Using fallback lexical index (neural model not active).")
            return True

        try:
            texts = [chunk.text for chunk in self.chunks]
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,  # L2 normalization for Inner Product = Cosine Similarity
            )
            embeddings = embeddings.astype(np.float32)

            dim = embeddings.shape[1]
            self.embedding_dimension = dim
            # FAISS IndexFlatIP for exact cosine similarity
            index = faiss.IndexFlatIP(dim)
            index.add(embeddings)
            self.faiss_index = index
            return True

        except Exception as e:
            logger.error(f"Error building FAISS index: {e}")
            self.faiss_index = None
            return False

    def search(
        self,
        query: str,
        top_k: int = 4,
        score_threshold: float = 0.25,
    ) -> List[Tuple[TextChunk, float]]:
        """
        Searches the index for passages relevant to the query.
        Returns a list of (TextChunk, similarity_score) sorted descending by score.
        Scores range from -1.0 to 1.0 (Cosine similarity).
        """
        if not self.chunks or not query.strip():
            return []

        # Use FAISS neural search if ready
        if self.is_neural_ready and self.faiss_index is not None:
            try:
                q_emb = self.model.encode(
                    [query],
                    show_progress_bar=False,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                ).astype(np.float32)

                effective_k = min(top_k, len(self.chunks))
                scores, indices = self.faiss_index.search(q_emb, effective_k)

                results: List[Tuple[TextChunk, float]] = []
                for score, idx in zip(scores[0], indices[0]):
                    if idx >= 0 and idx < len(self.chunks):
                        f_score = float(score)
                        if f_score >= score_threshold:
                            results.append((self.chunks[idx], round(f_score, 4)))

                return results
            except Exception as e:
                logger.error(f"FAISS search failed, falling back to lexical search: {e}")

        # Fallback search
        return self.fallback_retriever.search(query, top_k=top_k)

    def save_to_disk(self, index_name: str = "regu_index") -> bool:
        """Saves FAISS index and chunk metadata to data/processed/."""
        try:
            meta_path = self.processed_dir / f"{index_name}_chunks.pkl"
            with open(meta_path, "wb") as f:
                pickle.dump(self.chunks, f)

            if self.faiss_index is not None and HAS_FAISS:
                faiss_path = self.processed_dir / f"{index_name}.faiss"
                faiss.write_index(self.faiss_index, str(faiss_path))

            info_path = self.processed_dir / f"{index_name}_info.json"
            info = {
                "model_name": self.model_name,
                "num_chunks": len(self.chunks),
                "is_neural_ready": self.is_neural_ready,
                "dimension": self.embedding_dimension,
            }
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(info, f, indent=2)

            return True
        except Exception as e:
            logger.error(f"Failed to save index to disk: {e}")
            return False

    def load_from_disk(self, index_name: str = "regu_index") -> bool:
        """Loads FAISS index and chunk metadata from disk if available."""
        meta_path = self.processed_dir / f"{index_name}_chunks.pkl"
        faiss_path = self.processed_dir / f"{index_name}.faiss"

        if not meta_path.exists():
            return False

        try:
            with open(meta_path, "rb") as f:
                self.chunks = pickle.load(f)

            self.fallback_retriever.fit(self.chunks)

            if faiss_path.exists() and HAS_FAISS:
                self.faiss_index = faiss.read_index(str(faiss_path))
                self.is_neural_ready = True
            else:
                self.faiss_index = None

            return True
        except Exception as e:
            logger.error(f"Failed to load index from disk: {e}")
            return False

    def clear(self):
        """Clears memory and index."""
        self.chunks = []
        self.faiss_index = None
        self.fallback_retriever = FallbackLexicalRetriever()
