"""
tests/test_rag_pipeline.py - Tests for Vector Indexing, Evidence Retrieval, and Grounded RAG
"""

import pytest
from src.document_loader import DocumentLoader
from src.text_processor import TextProcessor
from src.vector_store import VectorStore
from src.rag_pipeline import RAGPipeline, RAGResponse


@pytest.fixture(scope="module")
def indexed_vector_store():
    """Builds a vector store with synthetic KYC direction chunks for testing."""
    loader = DocumentLoader(raw_data_dir="tests/fixtures")
    doc = loader.load_pdf(
        "tests/fixtures/synthetic_kyc_baseline_2016.pdf",
        publication_date="2016-02-25",
        source_url="https://rbi.org.in/synthetic-test-v1",
        title_override="Master Direction - KYC Directions 2016",
    )
    processor = TextProcessor(chunk_size_chars=500, chunk_overlap_chars=100)
    chunks = processor.chunk_document(doc)

    store = VectorStore(model_name="all-MiniLM-L6-v2", processed_dir="data/processed")
    store.build_index(chunks)
    return store


@pytest.fixture
def pipeline(indexed_vector_store):
    return RAGPipeline(
        vector_store=indexed_vector_store,
        similarity_threshold=0.20,
        top_k=3,
    )


def test_vector_retrieval_finds_relevant_chunk(indexed_vector_store):
    """Verifies that vector retrieval returns correct passage and page numbers for a KYC query."""
    query = "What are the Officially Valid Documents OVD for customer identification?"
    results = indexed_vector_store.search(query, top_k=2)

    assert len(results) > 0
    top_chunk, score = results[0]
    assert score > 0.0
    assert "Officially Valid Documents" in top_chunk.text or "Passport" in top_chunk.text
    assert 2 in top_chunk.page_numbers
    assert top_chunk.publication_date == "2016-02-25"
    assert top_chunk.source_url == "https://rbi.org.in/synthetic-test-v1"


def test_unsupported_question_insufficient_evidence(pipeline):
    """Verifies that queries with no relevant evidence trigger safe fallback message."""
    query = "What will RBI announce regarding cryptocurrency interest rates in 2030?"
    # Use high threshold or off-topic query that yields no sufficient evidence
    response = pipeline.query(query, similarity_threshold=0.85)

    assert response.has_sufficient_evidence is False
    assert pipeline.INSUFFICIENT_EVIDENCE_MSG in response.answer
    assert len(response.citations) == 0


def test_rag_retrieval_only_mode(pipeline):
    """Verifies that forcing retrieval-only mode returns evidence without calling LLM."""
    query = "What is the timeline for periodic KYC update of high risk customers?"
    response = pipeline.query(query, force_retrieval_only=True)

    assert response.is_generated is False
    assert response.has_sufficient_evidence is True
    assert "Retrieval-Only Mode Active" in response.answer
    assert len(response.citations) > 0

    assert any(
        "High-risk" in c.passage_text or "two (2) years" in c.passage_text
        for c in response.citations
    )
    assert any(2 in c.page_numbers for c in response.citations)
    assert response.citations[0].publication_date == "2016-02-25"


def test_citation_integrity_and_disclaimer(pipeline):
    """Verifies that citations preserve exact document properties and include compliance disclaimer."""
    query = "Customer Due Diligence anonymous accounts"
    response = pipeline.query(query, force_retrieval_only=True)

    assert len(response.citations) > 0
    c = response.citations[0]
    assert c.doc_id != ""
    assert c.title != ""
    assert response.disclaimer is not None
    assert "does not constitute official legal advice" in response.disclaimer
