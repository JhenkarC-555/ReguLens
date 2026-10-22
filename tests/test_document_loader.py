"""
tests/test_document_loader.py - Tests for PDF Ingestion and Page Tracking
"""

import io
from pathlib import Path
import pytest
from src.document_loader import DocumentLoader, DocumentRecord, PageRecord


@pytest.fixture
def fixtures_dir():
    return Path("tests/fixtures")


@pytest.fixture
def loader():
    return DocumentLoader(raw_data_dir="tests/fixtures")


def test_pdf_extraction_and_page_metadata(loader, fixtures_dir):
    """Verifies that PDF text is correctly extracted page-by-page with 1-indexed numbers."""
    pdf_path = fixtures_dir / "synthetic_kyc_baseline_2016.pdf"
    doc_record = loader.load_pdf(
        file_source=pdf_path,
        source_url="https://www.rbi.org.in/synthetic-test-v1",
        publication_date="2016-02-25",
        title_override="Master Direction - KYC Directions 2016 (Synthetic)",
    )

    assert doc_record.has_extractable_text is True
    assert doc_record.total_pages == 2
    assert len(doc_record.pages) == 2

    # Check page 1 metadata and content
    p1 = doc_record.pages[0]
    assert p1.page_number == 1
    assert "Customer Due Diligence" in p1.text
    assert p1.is_empty is False

    # Check page 2 metadata and content
    p2 = doc_record.pages[1]
    assert p2.page_number == 2
    assert "Officially Valid Documents" in p2.text
    assert "Passport" in p2.text

    # Check document-level metadata
    assert doc_record.publication_date == "2016-02-25"
    assert doc_record.source_url == "https://www.rbi.org.in/synthetic-test-v1"
    assert "KYC" in doc_record.title


def test_empty_pdf_handling(loader, fixtures_dir):
    """Verifies that empty PDF without text is handled safely without crashing."""
    empty_pdf = fixtures_dir / "synthetic_empty.pdf"
    doc_record = loader.load_pdf(empty_pdf)

    assert doc_record.total_pages >= 0
    # Text char count should be 0 or empty
    total_chars = sum(p.char_count for p in doc_record.pages)
    assert total_chars == 0
    assert doc_record.has_extractable_text is False


def test_scanned_image_pdf_ocr_warning(loader, fixtures_dir):
    """Verifies that image-only PDF triggers OCR required notice without fabricating text."""
    scanned_pdf = fixtures_dir / "synthetic_scanned_image.pdf"
    doc_record = loader.load_pdf(scanned_pdf)

    assert doc_record.ocr_required is True
    assert doc_record.extraction_warning is not None
    assert "OCR" in doc_record.extraction_warning
    # Should not fabricate text
    assert sum(p.char_count for p in doc_record.pages) == 0


def test_missing_file_handling(loader):
    """Verifies that non-existent PDF files return an error record instead of raising unhandled exception."""
    doc_record = loader.load_pdf("non_existent_file.pdf")
    assert doc_record.has_extractable_text is False
    assert "File does not exist" in (doc_record.extraction_warning or "")


def test_bytesio_stream_loading(loader, fixtures_dir):
    """Verifies that PDFs uploaded via in-memory BytesIO (Streamlit file uploader) work identically."""
    pdf_path = fixtures_dir / "synthetic_kyc_baseline_2016.pdf"
    with open(pdf_path, "rb") as f:
        bytes_data = io.BytesIO(f.read())

    doc_record = loader.load_pdf(
        file_source=bytes_data,
        filename="uploaded_memory.pdf",
    )
    assert doc_record.has_extractable_text is True
    assert doc_record.total_pages == 2
    assert doc_record.filename == "uploaded_memory.pdf"
