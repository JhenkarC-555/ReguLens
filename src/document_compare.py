"""
src/document_compare.py - ReguLens Regulatory Document Comparison Module
Compares two regulatory documents or version drafts using Python's standard difflib.
Categorizes changes into Additions, Removals, and Modifications, providing side-by-side
comparisons while strictly distinguishing wording differences from legal conclusions.
"""

from __future__ import annotations
import difflib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.document_loader import DocumentRecord


@dataclass
class DiffEntry:
    """Represents a text fragment that was added or removed."""
    line_number: int
    text: str
    section_context: Optional[str] = None


@dataclass
class DiffModification:
    """Represents a modified passage showing original wording beside changed wording."""
    block_index: int
    original_text: str
    changed_text: str
    similarity: float
    section_context: Optional[str] = None


@dataclass
class ComparisonResult:
    """Comprehensive comparison report between two documents or revisions."""
    doc_a_name: str
    doc_b_name: str
    doc_a_title: str
    doc_b_title: str
    overall_similarity_ratio: float  # 0.0 to 1.0
    additions: List[DiffEntry] = field(default_factory=list)
    removals: List[DiffEntry] = field(default_factory=list)
    modifications: List[DiffModification] = field(default_factory=list)
    unchanged_blocks_count: int = 0
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = (
        "LEGAL NOTICE: Detected differences reflect textual changes computed via SequenceMatcher. "
        "A wording difference does not necessarily constitute an official legal amendment, "
        "nor does identical wording confirm contemporary regulatory validity."
    )

    @property
    def total_changes_count(self) -> int:
        return len(self.additions) + len(self.removals) + len(self.modifications)


class DocumentComparator:
    """
    Compares regulatory documents at paragraph and line levels using difflib.
    Handles layout variance, section alignment, and whitespace normalization.
    """

    def __init__(
        self,
        similarity_threshold_for_modification: float = 0.40,
        min_change_length_chars: int = 4,
    ):
        self.mod_threshold = similarity_threshold_for_modification
        self.min_change_length_chars = min_change_length_chars

    @staticmethod
    def normalize_text_for_comparison(text: str) -> str:
        """
        Conservative normalization:
        - Normalizes line breaks
        - Collapses repeated horizontal whitespace
        - Preserves punctuation, numbers, capitalization, and clause labels
        """
        if not text:
            return ""
        norm = text.replace("\r\n", "\n").replace("\r", "\n")
        norm = re.sub(r"[ \t]+", " ", norm)
        lines = [line.strip() for line in norm.splitlines()]
        return "\n".join(lines).strip()

    def compare_documents(
        self,
        doc_a: DocumentRecord,
        doc_b: DocumentRecord,
    ) -> ComparisonResult:
        """Compares two DocumentRecords and returns a structured ComparisonResult."""
        warnings: List[str] = []

        if not doc_a.has_extractable_text or not doc_b.has_extractable_text:
            warnings.append(
                "One or both documents contain no extractable text. Comparison cannot be performed reliably."
            )
            return ComparisonResult(
                doc_a_name=doc_a.filename,
                doc_b_name=doc_b.filename,
                doc_a_title=doc_a.title,
                doc_b_title=doc_b.title,
                overall_similarity_ratio=0.0,
                warnings=warnings,
            )

        # Check for potential mismatch in document scopes
        if doc_a.doc_id == doc_b.doc_id:
            warnings.append("Comparing a document with itself. All sections are identical.")

        text_a = self.normalize_text_for_comparison(doc_a.full_text)
        text_b = self.normalize_text_for_comparison(doc_b.full_text)

        return self.compare_texts(
            text_a=text_a,
            text_b=text_b,
            name_a=doc_a.filename,
            name_b=doc_b.filename,
            title_a=doc_a.title,
            title_b=doc_b.title,
            extra_warnings=warnings,
        )

    def compare_texts(
        self,
        text_a: str,
        text_b: str,
        name_a: str = "Document A (Original)",
        name_b: str = "Document B (Revised)",
        title_a: str = "Original Version",
        title_b: str = "Revised Version",
        extra_warnings: Optional[List[str]] = None,
    ) -> ComparisonResult:
        """
        Core comparison algorithm using difflib.SequenceMatcher.
        Splits into paragraphs/sentences and identifies:
        - Exact unchanged blocks
        - Substituted / Modified blocks (paired original vs changed)
        - Pure Additions
        - Pure Removals
        """
        warnings = list(extra_warnings or [])

        # Compute overall textual similarity ratio on character/token text
        string_matcher = difflib.SequenceMatcher(None, text_a, text_b)
        overall_ratio = round(string_matcher.ratio(), 4)

        # Split into normalized non-empty lines for detailed diffing
        lines_a = [line.strip() for line in text_a.splitlines() if line.strip()]
        lines_b = [line.strip() for line in text_b.splitlines() if line.strip()]

        if not lines_a and not lines_b:
            return ComparisonResult(
                doc_a_name=name_a,
                doc_b_name=name_b,
                doc_a_title=title_a,
                doc_b_title=title_b,
                overall_similarity_ratio=1.0,
                warnings=["Both text inputs are empty."],
            )

        if overall_ratio < 0.20 and (lines_a and lines_b):
            warnings.append(
                "Warning: Low overall textual similarity (< 20%). These documents appear to be substantially "
                "different regulations or independently structured circulars rather than revisions of the same direction."
            )

        additions: List[DiffEntry] = []
        removals: List[DiffEntry] = []
        modifications: List[DiffModification] = []
        unchanged_count = 0
        mod_index = 1

        matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                unchanged_count += (i2 - i1)

            elif tag == "replace":
                slice_a = lines_a[i1:i2]
                slice_b = lines_b[j1:j2]

                # Pair up corresponding paragraphs as modifications where possible
                min_len = min(len(slice_a), len(slice_b))
                for k in range(min_len):
                    pa = slice_a[k]
                    pb = slice_b[k]
                    sim = difflib.SequenceMatcher(None, pa, pb).ratio()

                    if sim >= self.mod_threshold:
                        modifications.append(
                            DiffModification(
                                block_index=mod_index,
                                original_text=pa,
                                changed_text=pb,
                                similarity=round(sim, 3),
                                section_context=self._extract_section_context(pa),
                            )
                        )
                        mod_index += 1
                    else:
                        removals.append(
                            DiffEntry(
                                line_number=i1 + k + 1,
                                text=pa,
                                section_context=self._extract_section_context(pa),
                            )
                        )
                        additions.append(
                            DiffEntry(
                                line_number=j1 + k + 1,
                                text=pb,
                                section_context=self._extract_section_context(pb),
                            )
                        )

                # Excess in A are removals
                if len(slice_a) > min_len:
                    for k in range(min_len, len(slice_a)):
                        pa = slice_a[k]
                        removals.append(
                            DiffEntry(
                                line_number=i1 + k + 1,
                                text=pa,
                                section_context=self._extract_section_context(pa),
                            )
                        )

                # Excess in B are additions
                if len(slice_b) > min_len:
                    for k in range(min_len, len(slice_b)):
                        pb = slice_b[k]
                        additions.append(
                            DiffEntry(
                                line_number=j1 + k + 1,
                                text=pb,
                                section_context=self._extract_section_context(pb),
                            )
                        )

            elif tag == "delete":
                for idx, pa in enumerate(lines_a[i1:i2]):
                    removals.append(
                        DiffEntry(
                            line_number=i1 + idx + 1,
                            text=pa,
                            section_context=self._extract_section_context(pa),
                        )
                    )

            elif tag == "insert":
                for idx, pb in enumerate(lines_b[j1:j2]):
                    additions.append(
                        DiffEntry(
                            line_number=j1 + idx + 1,
                            text=pb,
                            section_context=self._extract_section_context(pb),
                        )
                    )

        return ComparisonResult(
            doc_a_name=name_a,
            doc_b_name=name_b,
            doc_a_title=title_a,
            doc_b_title=title_b,
            overall_similarity_ratio=overall_ratio,
            additions=additions,
            removals=removals,
            modifications=modifications,
            unchanged_blocks_count=unchanged_count,
            warnings=warnings,
        )

    @staticmethod
    def _extract_section_context(text: str) -> Optional[str]:
        """Looks for section or clause headers in the text."""
        match = re.search(
            r"(?:Section|Chapter|Clause|Rule|Part|Paragraph)\s+([0-9A-Za-z\.\(\)\-]+)",
            text,
            re.IGNORECASE,
        )
        if match:
            return match.group(0)
        return None

    @staticmethod
    def generate_html_side_by_side(text_a: str, text_b: str) -> str:
        """
        Generates a standard difflib HtmlDiff table for visual inspection.
        """
        lines_a = text_a.splitlines()
        lines_b = text_b.splitlines()
        differ = difflib.HtmlDiff(wrapcolumn=60)
        return differ.make_table(lines_a, lines_b, context=True, numlines=2)
