"""
app.py - ReguLens: Evidence-Based RBI Regulatory Change Intelligence Using RAG
Fullstack Streamlit Web Application providing grounded regulatory Q&A,
side-by-side document comparison, verified citations, and audit traceability.
"""

from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st

from src.document_loader import DocumentLoader, DocumentRecord
from src.text_processor import TextProcessor, TextChunk
from src.vector_store import VectorStore
from src.rag_pipeline import RAGPipeline, RAGResponse, CitationRecord
from src.document_compare import DocumentComparator, ComparisonResult

# -----------------------------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ReguLens — RBI Regulatory Intelligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Custom Styling (Fintech Aesthetic, High Legibility, Responsive Diff Views)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Brand Header Banner */
    .brand-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0369a1 100%);
        color: #ffffff;
        padding: 24px 28px;
        border-radius: 12px;
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
    }
    .brand-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
        color: #f8fafc;
    }
    .brand-subtitle {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-top: 4px;
        font-weight: 400;
    }
    .badge-tag {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-right: 8px;
    }
    .badge-primary { background-color: #0284c7; color: white; }
    .badge-success { background-color: #059669; color: white; }
    .badge-warning { background-color: #d97706; color: white; }
    .badge-secondary { background-color: #475569; color: white; }

    /* Card styling */
    .regu-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    @media (prefers-color-scheme: dark) {
        .regu-card {
            background-color: #1e293b;
            border-color: #334155;
            color: #f1f5f9;
        }
    }

    /* Citation Passage Box */
    .citation-box {
        border-left: 4px solid #0284c7;
        background-color: rgba(2, 132, 199, 0.05);
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin-top: 8px;
        font-size: 0.92rem;
        line-height: 1.5;
    }

    /* Diff Highlight Panels */
    .diff-addition {
        background-color: rgba(16, 185, 129, 0.12);
        border-left: 4px solid #10b981;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        margin-bottom: 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
    }
    .diff-removal {
        background-color: rgba(239, 68, 68, 0.12);
        border-left: 4px solid #ef4444;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        margin-bottom: 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
    }
    .diff-mod-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 14px;
    }
    @media (prefers-color-scheme: dark) {
        .diff-mod-box {
            background-color: #0f172a;
            border-color: #334155;
        }
    }

    /* Metric highlights */
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0284c7;
    }
    .metric-label {
        font-size: 0.82rem;
        text-transform: uppercase;
        color: #64748b;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "documents" not in st.session_state:
    st.session_state.documents: List[DocumentRecord] = []
if "chunks" not in st.session_state:
    st.session_state.chunks: List[TextChunk] = []
if "vector_store" not in st.session_state:
    st.session_state.vector_store: Optional[VectorStore] = None
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline: Optional[RAGPipeline] = None
if "last_rag_response" not in st.session_state:
    st.session_state.last_rag_response: Optional[RAGResponse] = None
if "last_comparison" not in st.session_state:
    st.session_state.last_comparison: Optional[ComparisonResult] = None
if "query_input_text" not in st.session_state:
    st.session_state.query_input_text = ""


@st.cache_resource
def get_core_services():
    """Initializes and caches DocumentLoader, TextProcessor, and VectorStore."""
    loader = DocumentLoader(raw_data_dir="data/raw")
    processor = TextProcessor(chunk_size_chars=1200, chunk_overlap_chars=200)
    vstore = VectorStore(model_name="all-MiniLM-L6-v2", processed_dir="data/processed")
    comparator = DocumentComparator()
    return loader, processor, vstore, comparator


loader, processor, vector_store, comparator = get_core_services()

# Auto-initialize session vector store if not set
if st.session_state.vector_store is None:
    st.session_state.vector_store = vector_store


def rebuild_index():
    """Extracts text and chunks from all currently loaded documents and builds the vector index."""
    all_chunks = processor.chunk_documents(st.session_state.documents)
    st.session_state.chunks = all_chunks
    st.session_state.vector_store.build_index(all_chunks)
    st.session_state.vector_store.save_to_disk("regu_index")
    # Initialize RAG Pipeline
    st.session_state.rag_pipeline = RAGPipeline(
        vector_store=st.session_state.vector_store,
        ollama_model="llama3.2:3b",
        similarity_threshold=st.session_state.get("sim_thresh", 0.22),
        top_k=st.session_state.get("top_k_val", 4),
    )


def load_default_fixtures_if_empty():
    """Automatically loads sample RBI regulatory directions if no documents are loaded."""
    if not st.session_state.documents:
        raw_dir = Path("data/raw")
        if not raw_dir.exists():
            raw_dir = Path("tests/fixtures")

        if raw_dir.exists():
            meta_registry = {
                "synthetic_kyc_baseline_2016.pdf": {
                    "title": "Master Direction - KYC Directions, 2016 (Baseline)",
                    "date": "2016-02-25",
                    "url": "https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx?did=338",
                },
                "synthetic_kyc_revised_2023.pdf": {
                    "title": "Master Direction - KYC Directions (Revised 2023)",
                    "date": "2023-05-04",
                    "url": "https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx?id=11566",
                },
                "rbi_digital_lending_guidelines_2022.pdf": {
                    "title": "Guidelines on Digital Lending (2022)",
                    "date": "2022-09-02",
                    "url": "https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=12382&fn=2&Mode=0",
                },
                "rbi_fldg_digital_lending_2023.pdf": {
                    "title": "Guidelines on Default Loss Guarantee (FLDG) in Digital Lending (2023)",
                    "date": "2023-06-08",
                    "url": "https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=12514&fn=2&Mode=0",
                },
                "rbi_payment_aggregators_directions.pdf": {
                    "title": "Guidelines on Regulation of Payment Aggregators (PA) & Gateways (PG)",
                    "date": "2020-03-17",
                    "url": "https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=11822&fn=9&Mode=0",
                },
                "rbi_credit_card_directions_2022.pdf": {
                    "title": "Master Direction - Credit Card and Debit Card Issuance (2022)",
                    "date": "2022-04-21",
                    "url": "https://www.rbi.org.in/scripts/BS_ViewMasterDirections.aspx?id=12300",
                },
            }

            records = []
            for pdf_name, info in meta_registry.items():
                p_path = raw_dir / pdf_name
                if p_path.exists():
                    rec = loader.load_pdf(
                        file_source=p_path,
                        filename=pdf_name,
                        source_url=info["url"],
                        publication_date=info["date"],
                        title_override=info["title"],
                    )
                    records.append(rec)

            if records:
                st.session_state.documents = records
                rebuild_index()


# Ensure baseline documents are loaded initially
load_default_fixtures_if_empty()

# -----------------------------------------------------------------------------
# Sidebar: System Status & Intelligence Controls
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ ReguLens Controls")

    # Document upload
    st.markdown("#### 📥 Ingest RBI Document")
    uploaded_files = st.file_uploader(
        "Upload RBI Master Direction / Circular PDF",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload official RBI regulatory PDFs to index and query.",
    )

    if uploaded_files:
        new_count = 0
        existing_filenames = {d.filename for d in st.session_state.documents}
        for up_file in uploaded_files:
            if up_file.name not in existing_filenames:
                rec = loader.load_pdf(
                    file_source=up_file,
                    filename=up_file.name,
                    title_override=up_file.name.replace(".pdf", "").replace("_", " "),
                )
                st.session_state.documents.append(rec)
                new_count += 1
        if new_count > 0:
            rebuild_index()
            st.success(f"Indexed {new_count} new document(s)!")

    # System Status Monitor
    st.markdown("---")
    st.markdown("#### 📡 System Status")

    # Check Ollama
    if st.session_state.rag_pipeline:
        ollama_ok, models, err = st.session_state.rag_pipeline.check_ollama_status()
    else:
        ollama_ok, models, err = False, [], "Pipeline not initialized"

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.markdown(
            f"**Indexed Docs:** `{len(st.session_state.documents)}`\n\n"
            f"**Chunks:** `{len(st.session_state.chunks)}`"
        )
    with col_s2:
        st.markdown(
            f"**FAISS:** `{'🟢 Active' if vector_store.is_neural_ready else '🟡 Lexical'}`\n\n"
            f"**Ollama:** `{'🟢 Online' if ollama_ok else '🟠 Offline'}`"
        )

    if ollama_ok and models:
        st.caption(f"Active LLM: `{models[0]}` (Port 11434)")
    elif not ollama_ok:
        st.caption("ℹ️ Ollama offline. Operating in Retrieval-Only Mode with verified citations.")

    # Execution Parameters
    st.markdown("---")
    st.markdown("#### 🎛️ Pipeline Parameters")

    force_retrieval = st.toggle(
        "Force Retrieval-Only Mode",
        value=not ollama_ok,
        help="Bypasses LLM generation to inspect exact retrieved regulatory evidence without generation latency.",
    )

    sim_thresh = st.slider(
        "Relevance Threshold (Cosine Sim)",
        min_value=0.10,
        max_value=0.80,
        value=0.22,
        step=0.02,
        help="Passages scoring below this threshold are rejected to prevent hallucination.",
        key="sim_thresh",
    )

    top_k_val = st.slider(
        "Top-K Evidence Passages",
        min_value=1,
        max_value=6,
        value=3,
        step=1,
        key="top_k_val",
    )

    if st.button("🔄 Reload Synthetic Sample Directions", use_container_width=True):
        st.session_state.documents = []
        load_default_fixtures_if_empty()
        st.rerun()

# -----------------------------------------------------------------------------
# Main Application Header Banner
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div class="brand-banner">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 class="brand-title">ReguLens</h1>
                <div class="brand-subtitle">Evidence-Based RBI Regulatory Change Intelligence Using RAG</div>
            </div>
            <div>
                <span class="badge-tag badge-primary">FAISS Vector Index</span>
                <span class="badge-tag badge-success">PyMuPDF Ingestion</span>
                <span class="badge-tag badge-warning">Zero-Hallucination Fallback</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Main Navigation Tabs
# -----------------------------------------------------------------------------
tab_ask, tab_compare, tab_repo, tab_eval = st.tabs(
    [
        "🔍 Ask Documents",
        "⚖️ Compare Regulations",
        "📚 Ingested Documents",
        "🧪 Hackathon Evaluation Matrix",
    ]
)

# =============================================================================
# TAB 1: ASK DOCUMENTS
# =============================================================================
with tab_ask:
    st.markdown("### Grounded Regulatory Question Answering")
    st.markdown(
        "Ask questions about the indexed Reserve Bank of India documents. "
        "Answers are strictly grounded in retrieved regulatory passages, with verifiable page numbers and sources."
    )

    # Clickable Question Pills
    st.markdown("**Sample Regulatory Inquiries:**")
    example_cols = st.columns(3)
    with example_cols[0]:
        if st.button("📄 What are Officially Valid Documents (OVD)?", use_container_width=True):
            st.session_state.query_input_text = "What documents can be accepted as Officially Valid Documents for KYC?"
    with example_cols[1]:
        if st.button("⏱️ Periodic KYC update timelines?", use_container_width=True):
            st.session_state.query_input_text = "What is the periodic KYC updation schedule for high, medium, and low-risk customers?"
    with example_cols[2]:
        if st.button("📹 Is Video KYC (V-CIP) permitted?", use_container_width=True):
            st.session_state.query_input_text = "What are the rules regarding Video-based Customer Identification Process (V-CIP)?"

    # Unsupported Question Test Pill
    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        if st.button("🚫 Test Safe Fallback: Unsupported Query", use_container_width=True):
            st.session_state.query_input_text = "What will RBI announce regarding cryptocurrency interest rates in 2030?"
    with sub_col2:
        if st.button("👤 Customer Acceptance & Anonymous Accounts", use_container_width=True):
            st.session_state.query_input_text = "What are the rules on opening accounts in anonymous or fictitious names?"

    # Query Input Box
    user_query = st.text_input(
        "Enter your regulatory question:",
        value=st.session_state.query_input_text,
        placeholder="e.g. Which documents are accepted as proof of identity under KYC directions?",
    )

    col_btn, col_clear = st.columns([1, 5])
    with col_btn:
        submit_query = st.button("🔍 Submit Inquiry", type="primary", use_container_width=True)

    if submit_query and user_query.strip():
        if not st.session_state.rag_pipeline:
            st.error("RAG Pipeline is not ready. Please ensure documents are loaded.")
        else:
            with st.spinner("Retrieving verified passages and evaluating regulatory evidence..."):
                resp = st.session_state.rag_pipeline.query(
                    question=user_query.strip(),
                    top_k=top_k_val,
                    similarity_threshold=sim_thresh,
                    force_retrieval_only=force_retrieval,
                )
                st.session_state.last_rag_response = resp

    # Render Results if available
    if st.session_state.last_rag_response:
        resp: RAGResponse = st.session_state.last_rag_response

        st.markdown("---")
        # Header with execution badges
        col_badge1, col_badge2, col_badge3 = st.columns([2, 2, 2])
        with col_badge1:
            if resp.is_generated:
                st.markdown(f"**Engine:** `🤖 Generated via {resp.model_used}`")
            else:
                st.markdown("**Engine:** `📋 Retrieval-Only Evidence Mode`")
        with col_badge2:
            evidence_status = "🟢 Sufficient Evidence Found" if resp.has_sufficient_evidence else "🔴 Insufficient Evidence"
            st.markdown(f"**Evidence Grounding:** `{evidence_status}`")
        with col_badge3:
            st.markdown(f"**Latency:** `{resp.execution_time_sec}s`")

        # Answer Box
        if not resp.has_sufficient_evidence:
            st.warning(f"⚠️ **{resp.answer}**")
            st.info(
                "ReguLens refuses to answer when the indexed documents lack verified regulatory evidence, "
                "preventing speculation and artificial hallucinations."
            )
        else:
            st.markdown("#### 💡 Answer")
            st.markdown(f"""<div class="regu-card">{resp.answer}</div>""", unsafe_allow_html=True)

        # Citations and Verified Passages
        if resp.citations:
            st.markdown(f"#### 📖 Verifiable Regulatory Citations ({len(resp.citations)})")
            st.caption("Each passage below was retrieved directly from indexed PDF pages and provided as ground truth.")

            for idx, c in enumerate(resp.citations, 1):
                pages_str = ", ".join(f"Page {p}" for p in c.page_numbers)
                date_str = f" • Published: {c.publication_date}" if c.publication_date else ""
                score_pct = int(c.similarity_score * 100) if c.similarity_score <= 1.0 else 100

                with st.expander(f"Passage {idx}: {c.title} ({pages_str}{date_str}) — Relevance Match: {score_pct}%", expanded=(idx == 1)):
                    st.markdown(f"**Source Document:** `{c.filename}` ({pages_str})")
                    if c.source_url:
                        st.markdown(f"[🔗 View Official Source Circular]({c.source_url})")

                    st.markdown(
                        f"""<div class="citation-box"><strong>Extracted Passage:</strong><br>{c.passage_text}</div>""",
                        unsafe_allow_html=True,
                    )

        # Disclaimer
        st.caption(f"⚖️ *{resp.disclaimer}*")

# =============================================================================
# TAB 2: COMPARE DOCUMENTS
# =============================================================================
with tab_compare:
    st.markdown("### ⚖️ Regulatory Document Comparison & Diff Intelligence")
    st.markdown(
        "Select two regulatory documents or version drafts to detect textual additions, removals, and wording modifications. "
        "Differences are computed using SequenceMatcher and presented with original and revised text side-by-side."
    )

    doc_names = [d.filename for d in st.session_state.documents]
    if len(doc_names) < 2:
        st.warning(
            "Please upload or load at least two documents in the sidebar or repository to perform a comparison."
        )
    else:
        col_doc_a, col_doc_b = st.columns(2)
        with col_doc_a:
            idx_a = 0
            sel_a = st.selectbox("Select Document A (Baseline / Earlier Version):", doc_names, index=idx_a)
        with col_doc_b:
            idx_b = min(1, len(doc_names) - 1)
            sel_b = st.selectbox("Select Document B (Revised / Amendment Version):", doc_names, index=idx_b)

        if st.button("⚖️ Compare Documents", type="primary"):
            doc_a_obj = next(d for d in st.session_state.documents if d.filename == sel_a)
            doc_b_obj = next(d for d in st.session_state.documents if d.filename == sel_b)

            with st.spinner("Analyzing text alignment, computing diffs, and categorizing changes..."):
                res = comparator.compare_documents(doc_a_obj, doc_b_obj)
                st.session_state.last_comparison = res

    if st.session_state.last_comparison:
        c_res: ComparisonResult = st.session_state.last_comparison

        st.markdown("---")
        # Legal Notice Disclaimer Banner
        st.warning(f"⚠️ {c_res.disclaimer}")

        if c_res.warnings:
            for w in c_res.warnings:
                st.info(f"ℹ️ {w}")

        # Metrics Row
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("Textual Similarity", f"{int(c_res.overall_similarity_ratio * 100)}%")
        with m_col2:
            st.metric("Modifications", len(c_res.modifications))
        with m_col3:
            st.metric("Additions", len(c_res.additions))
        with m_col4:
            st.metric("Removals", len(c_res.removals))

        # Diff View Tabs
        diff_tab1, diff_tab2, diff_tab3, diff_tab4 = st.tabs(
            [
                f"📝 Modifications ({len(c_res.modifications)})",
                f"➕ Additions ({len(c_res.additions)})",
                f"➖ Removals ({len(c_res.removals)})",
                "📊 Full HTML Diff Table",
            ]
        )

        with diff_tab1:
            if not c_res.modifications:
                st.info("No paragraph-level modifications detected between the selected texts.")
            else:
                st.markdown("##### Side-by-Side Wording Comparison")
                for mod in c_res.modifications:
                    st.markdown(
                        f"""
                        <div class="diff-mod-box">
                            <div style="font-weight: 600; font-size: 0.85rem; color: #64748b; margin-bottom: 8px;">
                                Change #{mod.block_index} {f'— Context: {mod.section_context}' if mod.section_context else ''} (Similarity: {int(mod.similarity * 100)}%)
                            </div>
                            <div style="display: flex; gap: 16px;">
                                <div style="flex: 1; border-left: 3px solid #ef4444; padding-left: 10px; font-size: 0.9rem;">
                                    <strong style="color: #ef4444;">Document A (Original Wording):</strong><br>
                                    {mod.original_text}
                                </div>
                                <div style="flex: 1; border-left: 3px solid #10b981; padding-left: 10px; font-size: 0.9rem;">
                                    <strong style="color: #10b981;">Document B (Revised Wording):</strong><br>
                                    {mod.changed_text}
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

        with diff_tab2:
            if not c_res.additions:
                st.info("No newly added text lines found in Document B.")
            else:
                st.markdown("##### Text Added in Document B")
                for add in c_res.additions:
                    ctx = f" [{add.section_context}]" if add.section_context else ""
                    st.markdown(
                        f"""<div class="diff-addition">+ Line {add.line_number}{ctx}: {add.text}</div>""",
                        unsafe_allow_html=True,
                    )

        with diff_tab3:
            if not c_res.removals:
                st.info("No removed text lines detected from Document A.")
            else:
                st.markdown("##### Text Removed from Document A")
                for rem in c_res.removals:
                    ctx = f" [{rem.section_context}]" if rem.section_context else ""
                    st.markdown(
                        f"""<div class="diff-removal">- Line {rem.line_number}{ctx}: {rem.text}</div>""",
                        unsafe_allow_html=True,
                    )

        with diff_tab4:
            st.markdown("##### Interactive HTML Sequence Diff")
            doc_a_obj = next((d for d in st.session_state.documents if d.filename == c_res.doc_a_name), None)
            doc_b_obj = next((d for d in st.session_state.documents if d.filename == c_res.doc_b_name), None)
            if doc_a_obj and doc_b_obj:
                html_table = comparator.generate_html_side_by_side(
                    doc_a_obj.full_text[:3000], doc_b_obj.full_text[:3000]
                )
                st.components.v1.html(
                    f"<div style='overflow-x:auto; font-family: monospace; font-size: 11px;'>{html_table}</div>",
                    height=500,
                    scrolling=True,
                )
            else:
                st.info("HTML diff table requires active document objects.")

# =============================================================================
# TAB 3: INGESTED DOCUMENTS REPOSITORY
# =============================================================================
with tab_repo:
    st.markdown("### 📚 Indexed Regulatory Document Repository")
    st.markdown("Review extracted text, page distributions, OCR alerts, and verified metadata.")

    if not st.session_state.documents:
        st.info("No documents are currently indexed.")
    else:
        for idx, doc in enumerate(st.session_state.documents, 1):
            with st.expander(f"📄 {idx}. {doc.title} ({doc.filename})", expanded=False):
                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    st.markdown(f"**Filename:** `{doc.filename}`")
                    st.markdown(f"**Total Pages:** `{doc.total_pages}`")
                with col_d2:
                    st.markdown(f"**Publication Date:** `{doc.publication_date or 'Not Verified'}`")
                    st.markdown(f"**OCR Required:** `{doc.ocr_required}`")
                with col_d3:
                    if doc.source_url:
                        st.markdown(f"[Official Source URL]({doc.source_url})")
                    if doc.extraction_warning:
                        st.warning(f"Extraction Note: {doc.extraction_warning}")

                st.markdown("**Page-by-Page Extraction Inspection:**")
                page_options = [f"Page {p.page_number} ({p.char_count} chars)" for p in doc.pages]
                if page_options:
                    selected_page_str = st.selectbox(
                        "Inspect Page Text:", page_options, key=f"page_sel_{doc.doc_id}"
                    )
                    page_num = int(selected_page_str.split()[1])
                    matching_page = next((p for p in doc.pages if p.page_number == page_num), None)
                    if matching_page:
                        st.text_area(
                            f"Text on Page {page_num}:",
                            value=matching_page.text,
                            height=220,
                            key=f"text_{doc.doc_id}_{page_num}",
                        )

# =============================================================================
# TAB 4: HACKATHON EVALUATION MATRIX & LIVE BENCHMARKS
# =============================================================================
with tab_eval:
    st.markdown("### 🧪 Evaluation & Failure Analysis Hub")
    st.markdown(
        "Live execution of the **5 Hackathon Test Questions** specified in the ReguLens implementation plan. "
        "Evaluates grounding, refusal handling, citation traceability, and intentional failure modes."
    )

    eval_test_cases = [
        {
            "id": "T1",
            "type": "Direct Lookup",
            "query": "What are the Officially Valid Documents (OVD) for KYC identification?",
            "expected": "Accurate list containing Passport, Aadhaar, Voter ID, Driving Licence with page citation.",
        },
        {
            "id": "T2",
            "type": "Specific Rule Detail",
            "query": "What is the periodic KYC updation schedule for high risk vs low risk customers?",
            "expected": "High risk at least once every 2 years; Low risk at least once every 10 years.",
        },
        {
            "id": "T3",
            "type": "Regulatory Evolution",
            "query": "What does the revised direction say about Video-based Customer Identification Process (V-CIP)?",
            "expected": "Section 4A V-CIP rules, real-time live interaction, facial matching and geotagging.",
        },
        {
            "id": "T4",
            "type": "Unsupported Query",
            "query": "What will RBI announce regarding cryptocurrency capital gains tax next year?",
            "expected": "Safe refusal: 'I couldn't find sufficient evidence in the selected documents.'",
        },
        {
            "id": "T5",
            "type": "Outdated / Status Conflict",
            "query": "Is digital KYC permitted under the 2016 baseline direction compared to revised 2023 direction?",
            "expected": "Distinguishes baseline from revised amendment, noting evolution of digital KYC provisions.",
        },
    ]

    if st.button("🚀 Run Live 5-Question Benchmark Suite", type="primary"):
        results_list = []
        with st.spinner("Executing benchmark queries against RAG pipeline..."):
            for tc in eval_test_cases:
                t_start = time.time()
                res = st.session_state.rag_pipeline.query(
                    question=tc["query"],
                    top_k=top_k_val,
                    similarity_threshold=sim_thresh,
                    force_retrieval_only=force_retrieval,
                )
                t_elapsed = round(time.time() - t_start, 2)
                results_list.append(
                    {
                        "ID": tc["id"],
                        "Category": tc["type"],
                        "Query": tc["query"],
                        "Grounding": "Grounded" if res.has_sufficient_evidence else "Safe Refusal",
                        "Citations": len(res.citations),
                        "Latency": f"{t_elapsed}s",
                        "Answer": res.answer,
                    }
                )

        st.session_state.benchmark_results = results_list

    if "benchmark_results" in st.session_state:
        st.markdown("#### Live Benchmark Results")
        st.dataframe(st.session_state.benchmark_results, use_container_width=True)

        for item in st.session_state.benchmark_results:
            with st.expander(f"Details: [{item['ID']}] {item['Category']} — {item['Grounding']}"):
                st.markdown(f"**Query:** {item['Query']}")
                st.markdown(f"**Response:**\n\n{item['Answer']}")

    st.markdown("---")
    st.markdown("#### 🔍 Documented Failure Analysis (Judging Rubric Requirement)")
    st.markdown(
        """
        1. **Failure Mode 1: Low-Text Scanned PDF Extraction**
           - *Cause:* Older RBI circulars published as scanned image-only raster PDFs contain zero extractable text streams.
           - *ReguLens Handling:* Instead of failing silently or inventing text, ReguLens triggers an explicit `ocr_required` warning in `DocumentLoader` explaining that OCR (e.g. Tesseract) is required.
        
        2. **Failure Mode 2: Unrelated Circular Comparison**
           - *Cause:* Comparing two circulars on completely unrelated subjects (e.g. KYC vs External Commercial Borrowings).
           - *ReguLens Handling:* SequenceMatcher identifies similarity < 20% and outputs an automated warning advising that documents are structurally unrelated rather than revised versions.
        """
    )
