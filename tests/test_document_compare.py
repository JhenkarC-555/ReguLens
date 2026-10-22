"""
tests/test_document_compare.py - Tests for Regulatory Document Comparison & Diffing
"""

import pytest
from src.document_loader import DocumentLoader
from src.document_compare import DocumentComparator, ComparisonResult


@pytest.fixture
def comparator():
    return DocumentComparator()


def test_compare_identical_documents(comparator):
    """Verifies that comparing identical documents produces 1.0 similarity and 0 changes."""
    text = (
        "Section 1. Short Title\n\n"
        "These Directions shall be called RBI KYC Directions, 2016.\n\n"
        "Section 2. Applicability\n\n"
        "These Directions apply to all Regulated Entities."
    )
    result = comparator.compare_texts(text, text, name_a="Draft 1", name_b="Draft 1 Copy")

    assert result.overall_similarity_ratio == 1.0
    assert len(result.additions) == 0
    assert len(result.removals) == 0
    assert len(result.modifications) == 0
    assert result.disclaimer is not None
    assert "LEGAL NOTICE" in result.disclaimer


def test_detect_additions_removals_modifications(comparator):
    """Verifies detection of added clauses, removed paragraphs, and modified wording."""
    text_a = (
        "Chapter I. Preliminary\n\n"
        "Section 1. Regulated Entities shall verify identity physically.\n\n"
        "Section 2. Old obsolete requirement for physical tokens."
    )
    text_b = (
        "Chapter I. Preliminary\n\n"
        "Section 1. Regulated Entities shall verify identity physically or digitally via V-CIP.\n\n"
        "Section 3. Newly inserted clause regarding online onboarding."
    )

    result = comparator.compare_texts(
        text_a=text_a,
        text_b=text_b,
        name_a="Version 2016",
        name_b="Version 2023",
    )

    # Overall similarity should be intermediate
    assert 0.2 < result.overall_similarity_ratio < 1.0

    # Section 1 should be detected as a modification
    assert len(result.modifications) >= 1
    mod = result.modifications[0]
    assert "physically" in mod.original_text
    assert "V-CIP" in mod.changed_text
    assert mod.similarity > 0.4

    # Section 2 should be in removals or additions
    assert len(result.removals) >= 1 or len(result.additions) >= 1


def test_compare_documents_from_synthetic_pdfs(comparator):
    """Verifies document comparison using actual synthetic PDF fixtures."""
    loader = DocumentLoader(raw_data_dir="tests/fixtures")
    doc_baseline = loader.load_pdf("tests/fixtures/synthetic_kyc_baseline_2016.pdf")
    doc_revised = loader.load_pdf("tests/fixtures/synthetic_kyc_revised_2023.pdf")

    result = comparator.compare_documents(doc_baseline, doc_revised)

    assert result.overall_similarity_ratio > 0.5
    assert len(result.modifications) >= 3
    assert len(result.additions) >= 3
    # V-CIP is an addition in revised 2023
    all_added_text = " ".join(a.text for a in result.additions) + " ".join(m.changed_text for m in result.modifications)
    assert "V-CIP" in all_added_text or "Video-based" in all_added_text
    assert result.disclaimer is not None
