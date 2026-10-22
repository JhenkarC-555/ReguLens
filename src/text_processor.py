"""
src/text_processor.py - ReguLens Text Processing & Chunking Module
Cleans regulatory text conservatively, preserving section numbering, legal definitions,
and clause markings. Produces structured chunks with full source and page metadata.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from src.document_loader import DocumentRecord, PageRecord


@dataclass
class TextChunk:
    """Represents an indexed passage linked to verified page and document metadata."""
    chunk_id: str
    doc_id: str
    filename: str
    title: str
    text: str
    page_numbers: List[int]
    publication_date: Optional[str] = None
    source_url: Optional[str] = None
    section_hint: Optional[str] = None
    char_count: int = 0
    token_count_approx: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextProcessor:
    """
    Cleans regulatory text and performs section-aware, overlapping chunking.
    Preserves clause structure, page numbers, and document citations.
    """

    def __init__(
        self,
        chunk_size_chars: int = 1400,    # Approx 350-450 tokens
        chunk_overlap_chars: int = 250,  # Overlap between contiguous chunks
        min_chunk_chars: int = 80,       # Ignore tiny fragmented noise
    ):
        self.chunk_size_chars = chunk_size_chars
        self.chunk_overlap_chars = chunk_overlap_chars
        self.min_chunk_chars = min_chunk_chars

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Cleans unnecessary formatting artifacts, trailing whitespace, and form feed characters
        while strictly preserving:
        - Section numbers (e.g., 'Section 3.1', '15(a)(i)')
        - Dates and monetary figures
        - Paragraph structure
        """
        if not text:
            return ""

        # Normalize Windows / Mac carriage returns
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

        # Replace non-breaking spaces and exotic whitespace with standard space
        cleaned = re.sub(r"[\u00A0\u2000-\u200B\u202F\u205F\u3000]", " ", cleaned)

        # Replace page break form feeds with double newlines
        cleaned = cleaned.replace("\x0c", "\n\n")

        # Remove redundant inline spaces/tabs while preserving linebreaks
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # Collapse more than two consecutive newlines into double newlines
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # Strip leading/trailing lines
        lines = [line.strip() for line in cleaned.splitlines()]
        cleaned = "\n".join(lines).strip()

        return cleaned

    def chunk_document(self, doc_record: DocumentRecord) -> List[TextChunk]:
        """
        Chunks an ingested document page-by-page to ensure every chunk
        is strictly traceable to an exact PDF page.
        """
        if not doc_record.has_extractable_text or not doc_record.pages:
            return []

        chunks: List[TextChunk] = []
        global_chunk_idx = 0

        for page in doc_record.pages:
            if page.is_empty or not page.text.strip():
                continue

            cleaned_page = self.clean_text(page.text)
            if len(cleaned_page) < self.min_chunk_chars:
                continue

            # Split page text into overlapping windows
            page_chunks = self._chunk_page_text(
                text=cleaned_page,
                doc_record=doc_record,
                page_num=page.page_number,
                start_idx=global_chunk_idx,
            )
            chunks.extend(page_chunks)
            global_chunk_idx += len(page_chunks)

        return chunks

    def chunk_documents(self, doc_records: List[DocumentRecord]) -> List[TextChunk]:
        """Chunks a collection of documents."""
        all_chunks: List[TextChunk] = []
        for doc in doc_records:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks

    def _chunk_page_text(
        self,
        text: str,
        doc_record: DocumentRecord,
        page_num: int,
        start_idx: int,
    ) -> List[TextChunk]:
        """
        Splits a single page's text using natural paragraph and clause breaks.
        """
        chunks: List[TextChunk] = []
        current_idx = start_idx

        # If page fits within chunk size, create a single chunk
        if len(text) <= self.chunk_size_chars:
            section_hint = self._detect_section_hint(text)
            chunk = TextChunk(
                chunk_id=f"{doc_record.doc_id}_p{page_num}_c{current_idx}",
                doc_id=doc_record.doc_id,
                filename=doc_record.filename,
                title=doc_record.title,
                text=text,
                page_numbers=[page_num],
                publication_date=doc_record.publication_date,
                source_url=doc_record.source_url,
                section_hint=section_hint,
                char_count=len(text),
                token_count_approx=len(text) // 4,
            )
            return [chunk]

        # Use natural paragraph splits first
        paragraphs = text.split("\n\n")
        buffer: List[str] = []
        buffer_len = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_len = len(para)

            # If a single paragraph is larger than chunk_size_chars, split by sentences
            if para_len > self.chunk_size_chars:
                if buffer:
                    combined_text = "\n\n".join(buffer).strip()
                    if len(combined_text) >= self.min_chunk_chars:
                        chunk = self._create_chunk(
                            text=combined_text,
                            doc_record=doc_record,
                            page_num=page_num,
                            idx=current_idx,
                        )
                        chunks.append(chunk)
                        current_idx += 1
                    buffer = []
                    buffer_len = 0

                # Sentence-level windowing for long paragraph
                sub_chunks = self._sliding_window_sentences(
                    para, doc_record, page_num, current_idx
                )
                chunks.extend(sub_chunks)
                current_idx += len(sub_chunks)
                continue

            if buffer_len + para_len > self.chunk_size_chars and buffer:
                combined_text = "\n\n".join(buffer).strip()
                if len(combined_text) >= self.min_chunk_chars:
                    chunk = self._create_chunk(
                        text=combined_text,
                        doc_record=doc_record,
                        page_num=page_num,
                        idx=current_idx,
                    )
                    chunks.append(chunk)
                    current_idx += 1

                # Retain overlap from end of previous buffer if possible
                overlap_text = buffer[-1] if buffer and len(buffer[-1]) <= self.chunk_overlap_chars else ""
                buffer = [overlap_text, para] if overlap_text else [para]
                buffer_len = sum(len(p) for p in buffer)
            else:
                buffer.append(para)
                buffer_len += para_len

        if buffer:
            combined_text = "\n\n".join(buffer).strip()
            if len(combined_text) >= self.min_chunk_chars:
                chunk = self._create_chunk(
                    text=combined_text,
                    doc_record=doc_record,
                    page_num=page_num,
                    idx=current_idx,
                )
                chunks.append(chunk)

        return chunks

    def _sliding_window_sentences(
        self,
        long_text: str,
        doc_record: DocumentRecord,
        page_num: int,
        start_idx: int,
    ) -> List[TextChunk]:
        """Sliding window fallback for dense continuous regulatory text without paragraph breaks."""
        chunks: List[TextChunk] = []
        sentences = re.split(r"(?<=[.!?])\s+", long_text)
        current_idx = start_idx
        window: List[str] = []
        window_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            s_len = len(sentence)
            if window_len + s_len > self.chunk_size_chars and window:
                text_slice = " ".join(window).strip()
                chunks.append(
                    self._create_chunk(text_slice, doc_record, page_num, current_idx)
                )
                current_idx += 1
                # Overlap: keep last sentence
                window = [window[-1], sentence] if len(window[-1]) <= self.chunk_overlap_chars else [sentence]
                window_len = sum(len(s) for s in window)
            else:
                window.append(sentence)
                window_len += s_len

        if window:
            text_slice = " ".join(window).strip()
            if len(text_slice) >= self.min_chunk_chars:
                chunks.append(
                    self._create_chunk(text_slice, doc_record, page_num, current_idx)
                )

        return chunks

    def _create_chunk(
        self,
        text: str,
        doc_record: DocumentRecord,
        page_num: int,
        idx: int,
    ) -> TextChunk:
        return TextChunk(
            chunk_id=f"{doc_record.doc_id}_p{page_num}_c{idx}",
            doc_id=doc_record.doc_id,
            filename=doc_record.filename,
            title=doc_record.title,
            text=text,
            page_numbers=[page_num],
            publication_date=doc_record.publication_date,
            source_url=doc_record.source_url,
            section_hint=self._detect_section_hint(text),
            char_count=len(text),
            token_count_approx=len(text) // 4,
        )

    @staticmethod
    def _detect_section_hint(text: str) -> Optional[str]:
        """Detects regulatory section or chapter headings in the passage."""
        match = re.search(
            r"(?:Section|Chapter|Clause|Rule|Part|Paragraph)\s+([0-9A-Za-z\.\(\)\-]+)",
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(0)
        return None
