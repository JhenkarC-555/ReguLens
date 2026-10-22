"""
tests/test_text_processor.py - Tests for Text Cleaning and Overlapping Chunking
"""

from pathlib import Path
import pytest
from src.document_loader import DocumentLoader, DocumentRecord, PageRecord
from src.text_processor import TextProcessor, TextChunk


@pytest.fixture
def processor():
    return TextProcessor(chunk_size_chars=400, chunk_overlap_chars=80, min_chunk_chars=30)


def test_clean_text_preserves_regulatory_sections(processor):
    """Verifies that cleaning removes excessive whitespace while preserving section numbering."""
    raw = "  Section  15(2)(a)  \r\n\r\n  Applicability   to   Banks.   \n\n\n\nRule   4.1  "
    cleaned = processor.clean_text(raw)
    assert "Section 15(2)(a)" in cleaned
    assert "Applicability to Banks." in cleaned
    assert "Rule 4.1" in cleaned
    assert "\r" not in cleaned
    assert "   " not in cleaned


def test_chunk_preserves_page_numbers_and_metadata(processor):
    """Verifies that each chunk is strictly tagged with its origin page number and document info."""
    loader = DocumentLoader(raw_data_dir="tests/fixtures")
    doc = loader.load_pdf(
        "tests/fixtures/synthetic_kyc_baseline_2016.pdf",
        publication_date="2016-02-25",
        source_url="https://rbi.org.in/synthetic-test",
    )

    chunks = processor.chunk_document(doc)
    assert len(chunks) >= 2

    # Verify that all chunks have valid page numbers and document IDs
    for chunk in chunks:
        assert chunk.doc_id == doc.doc_id
        assert chunk.filename == doc.filename
        assert chunk.publication_date == "2016-02-25"
        assert chunk.source_url == "https://rbi.org.in/synthetic-test"
        assert len(chunk.page_numbers) > 0
        assert chunk.page_numbers[0] in [1, 2]
        assert len(chunk.text) >= processor.min_chunk_chars

    # Page 2 chunk should contain OVD info
    ovd_chunks = [c for c in chunks if "Officially Valid Documents" in c.text]
    assert len(ovd_chunks) > 0
    assert ovd_chunks[0].page_numbers[0] == 2


def test_chunk_empty_document(processor):
    """Verifies that chunking an empty or non-extractable document yields empty list without error."""
    doc = DocumentRecord(
        doc_id="empty_doc",
        filename="empty.pdf",
        title="Empty Doc",
        has_extractable_text=False,
    )
    chunks = processor.chunk_document(doc)
    assert chunks == []
