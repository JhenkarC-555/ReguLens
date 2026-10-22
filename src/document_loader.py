"""
src/document_loader.py - ReguLens Document Ingestion Module
Extracts text and page-level metadata from RBI regulatory PDFs using PyMuPDF.
Supports both file paths and in-memory byte buffers (for Streamlit uploads).
"""

from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import io

try:
    import pymupdf  # PyMuPDF v1.24+
except ImportError:
    import fitz as pymupdf  # Legacy fallback


@dataclass
class PageRecord:
    """Represents an extracted page with its text and positional metadata."""
    page_number: int  # 1-indexed
    text: str
    char_count: int
    is_empty: bool = False
    ocr_suspected: bool = False


@dataclass
class DocumentRecord:
    """Represents an ingested regulatory document with page-by-page breakdown."""
    doc_id: str
    filename: str
    title: str
    publication_date: Optional[str] = None
    source_url: Optional[str] = None
    total_pages: int = 0
    pages: List[PageRecord] = field(default_factory=list)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)
    has_extractable_text: bool = True
    ocr_required: bool = False
    extraction_warning: Optional[str] = None

    @property
    def full_text(self) -> str:
        """Concatenates text across all pages with clear page markers."""
        return "\n\n".join(
            f"--- Page {p.page_number} ---\n{p.text}"
            for p in self.pages
            if p.text.strip()
        )


class DocumentLoader:
    """
    Ingests PDF documents, extracting text and preserving verified metadata.
    Does not fabricate dates, titles, or page numbers.
    """

    MIN_TEXT_CHARS_PER_PAGE = 30  # Threshold under which a page may be scanned/image-only

    def __init__(self, raw_data_dir: Optional[Union[str, Path]] = None):
        self.raw_data_dir = Path(raw_data_dir) if raw_data_dir else Path("data/raw")
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def load_pdf(
        self,
        file_source: Union[str, Path, io.BytesIO, bytes],
        filename: Optional[str] = None,
        source_url: Optional[str] = None,
        publication_date: Optional[str] = None,
        title_override: Optional[str] = None,
    ) -> DocumentRecord:
        """
        Loads and parses a PDF from a path, BytesIO, or raw bytes.

        Args:
            file_source: File path, BytesIO stream, or raw byte sequence.
            filename: Name of the file (inferred if path provided).
            source_url: Verified RBI source URL (not fabricated).
            publication_date: Verified publication date (YYYY-MM-DD or official format).
            title_override: Explicit title if known from official index.
        """
        doc = None
        inferred_filename = filename or "document.pdf"

        try:
            if isinstance(file_source, (str, Path)):
                path = Path(file_source)
                inferred_filename = filename or path.name
                if not path.exists():
                    return DocumentRecord(
                        doc_id=self._generate_doc_id(inferred_filename),
                        filename=inferred_filename,
                        title=title_override or inferred_filename,
                        has_extractable_text=False,
                        extraction_warning=f"File does not exist: {path}",
                    )
                doc = pymupdf.open(str(path))
            elif isinstance(file_source, io.BytesIO):
                stream_bytes = file_source.getvalue()
                doc = pymupdf.open(stream=stream_bytes, filetype="pdf")
            elif isinstance(file_source, bytes):
                doc = pymupdf.open(stream=file_source, filetype="pdf")
            else:
                raise ValueError(f"Unsupported file source type: {type(file_source)}")

            # Generate stable doc_id
            doc_id = self._generate_doc_id(inferred_filename)

            # Metadata extraction
            raw_meta = doc.metadata or {}
            extracted_title = (
                title_override
                or raw_meta.get("title")
                or self._infer_title_from_first_page(doc)
                or inferred_filename
            )

            # Check if PDF is completely empty (0 pages)
            total_pages = len(doc)
            if total_pages == 0:
                return DocumentRecord(
                    doc_id=doc_id,
                    filename=inferred_filename,
                    title=extracted_title,
                    source_url=source_url,
                    publication_date=publication_date,
                    total_pages=0,
                    has_extractable_text=False,
                    extraction_warning="PDF contains 0 pages.",
                    raw_metadata=raw_meta,
                )

            pages_records: List[PageRecord] = []
            low_text_page_count = 0
            total_chars = 0

            for page_idx in range(total_pages):
                page_num = page_idx + 1
                try:
                    page = doc[page_idx]
                    page_text = page.get_text("text") or ""
                    cleaned_text = page_text.strip()
                    char_len = len(cleaned_text)
                    total_chars += char_len

                    is_empty = char_len == 0
                    ocr_suspected = char_len < self.MIN_TEXT_CHARS_PER_PAGE

                    if ocr_suspected:
                        low_text_page_count += 1

                    pages_records.append(
                        PageRecord(
                            page_number=page_num,
                            text=cleaned_text,
                            char_count=char_len,
                            is_empty=is_empty,
                            ocr_suspected=ocr_suspected,
                        )
                    )
                except Exception as page_err:
                    pages_records.append(
                        PageRecord(
                            page_number=page_num,
                            text="",
                            char_count=0,
                            is_empty=True,
                            ocr_suspected=True,
                        )
                    )

            # Check if entire PDF or vast majority is image-only
            ocr_required = (low_text_page_count == total_pages and total_pages > 0)
            has_extractable_text = total_chars > 0

            warning = None
            if ocr_required:
                warning = (
                    "Scanned image PDF detected. Little or no machine-readable text found. "
                    "An external OCR pipeline (such as Tesseract OCR) would be required to extract text. "
                    "Note: ReguLens does not fabricate text for scanned documents without OCR."
                )
            elif low_text_page_count > 0:
                warning = (
                    f"{low_text_page_count} of {total_pages} page(s) contain very little or no machine-readable text "
                    "(possible scanned images or diagrams)."
                )

            return DocumentRecord(
                doc_id=doc_id,
                filename=inferred_filename,
                title=extracted_title.strip(),
                publication_date=publication_date,
                source_url=source_url,
                total_pages=total_pages,
                pages=pages_records,
                raw_metadata=raw_meta,
                has_extractable_text=has_extractable_text,
                ocr_required=ocr_required,
                extraction_warning=warning,
            )

        except Exception as e:
            return DocumentRecord(
                doc_id=self._generate_doc_id(inferred_filename),
                filename=inferred_filename,
                title=title_override or inferred_filename,
                has_extractable_text=False,
                extraction_warning=f"PDF parsing error: {str(e)}",
            )
        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass

    def load_directory(
        self,
        directory_path: Optional[Union[str, Path]] = None,
        metadata_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[DocumentRecord]:
        """
        Loads all PDF files from a target directory.
        Allows passing an optional metadata_map to attach verified official dates/titles.
        """
        target_dir = Path(directory_path) if directory_path else self.raw_data_dir
        if not target_dir.exists():
            return []

        pdf_files = sorted(list(target_dir.glob("*.pdf")) + list(target_dir.glob("*.PDF")))
        records: List[DocumentRecord] = []
        meta_dict = metadata_map or {}

        for pdf_path in pdf_files:
            file_meta = meta_dict.get(pdf_path.name, {})
            record = self.load_pdf(
                file_source=pdf_path,
                filename=pdf_path.name,
                source_url=file_meta.get("source_url"),
                publication_date=file_meta.get("publication_date"),
                title_override=file_meta.get("title"),
            )
            records.append(record)

        return records

    @staticmethod
    def _generate_doc_id(filename: str) -> str:
        """Generates a clean identifier from filename."""
        clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", filename)
        return clean.strip("_")

    @staticmethod
    def _infer_title_from_first_page(doc: pymupdf.Document) -> Optional[str]:
        """Attempts to infer document title from the first lines of page 1."""
        if len(doc) == 0:
            return None
        try:
            page1_text = doc[0].get_text("text") or ""
            lines = [line.strip() for line in page1_text.splitlines() if line.strip()]
            for line in lines[:5]:
                # Look for typical RBI headers or Master Direction labels
                if any(k in line.lower() for k in ["reserve bank", "master direction", "circular", "notification", "guidelines"]):
                    return line
            if lines:
                return lines[0][:120]
        except Exception:
            pass
        return None
