# ReguLens — Evidence-Based RBI Regulatory Change Intelligence Using RAG

> **Hackathon Track:** *From Text to Insight: Ask Your Documents*  
> **Institution:** Global Academy of Technology — Department of AI & ML  
> **Product Name:** **ReguLens**  
> **Subtitle:** Precision RBI Regulatory Change Intelligence & Grounded Question Answering  

---

## 1. Project Overview

**ReguLens** is an open-source, fullstack regulatory intelligence platform designed for compliance officers, fintech risk managers, and financial analysts. It solves the critical problem of navigating voluminous Reserve Bank of India (RBI) Master Directions, circulars, and amendments by combining:

1. **Strictly Grounded Regulatory Q&A:** A Retrieval-Augmented Generation (RAG) engine that answers inquiries *only* using retrieved regulatory text, enforcing zero-hallucination refusals and verifiable page citations.
2. **Regulatory Change Intelligence & Diffing:** A sequence-matching engine that inspects two versions of a regulatory document, categorizing differences into **Additions**, **Removals**, and **Modifications** with side-by-side wording views.
3. **Audit Traceability:** Retains exact page numbers, document titles, publication dates, and source URLs for every citation.

---

## 2. Problem Statement & Motivation

Fintechs and regulated banks in India operate under frequent regulatory updates issued by the Reserve Bank of India across Master Directions, notifications, and amendment circulars. Reading through 100+ page legal documents manually introduces critical operational risks:
- **Missed Compliance Mandates:** Subtle additions (such as Video-CIP requirements or periodic re-KYC timelines) are easily overlooked.
- **Hallucination Risk of Generic LLMs:** Public LLMs often invent regulatory circular numbers, assume outdated rules are valid, or provide legal interpretations without evidence.
- **Wording vs Legal Impact Confusion:** Automated text tools often mistake formatting differences for legal changes. ReguLens strictly isolates textual diffs from verified legal conclusions.

---

## 3. Core Features

### 🔍 Feature 1 — Ask RBI Documents (Grounded Q&A)
- Ingests official PDF circulars and Master Directions.
- Uses **Sentence Transformers** (`all-MiniLM-L6-v2`) and **FAISS** to retrieve top matching regulatory passages.
- Evaluates cosine similarity against a configurable relevance threshold.
- Generates precise, evidence-grounded answers via local **Ollama (`llama3.2:3b`)**.
- Displays verified citations with origin page numbers, document IDs, and official RBI links.

### 🚫 Feature 2 — Zero-Hallucination Safe Fallback
- If the retrieved evidence is insufficient or irrelevant, the system strictly outputs:
  > *"I couldn't find sufficient evidence in the selected documents."*
- Operates in a **Retrieval-Only Mode** if local LLM generation is unavailable or offline, preventing server crashes.

### ⚖️ Feature 3 — Regulatory Document Comparison & Diffing
- Compares two documents or revisions using Python's `difflib.SequenceMatcher`.
- Classifies changes into:
  - **Modifications:** Original wording vs revised wording side-by-side with similarity scores.
  - **Additions:** Newly inserted regulatory clauses.
  - **Removals:** Deprecated or repealed provisions.
- Embeds a mandatory legal disclaimer that textual differences are not definitive legal compliance certifications.

### 📊 Feature 4 — Evaluation & Benchmark Hub
- Includes a live test runner for the 5 hackathon test cases.
- Documents failure analysis (scanned raster PDFs, low-similarity circulars).

---

## 4. System Architecture

```mermaid
flowchart TD
    subgraph Ingestion ["1. Document Ingestion"]
        A[RBI PDF Files / Uploads] --> B[PyMuPDF Page Extractor]
        B --> C[OCR & Empty Page Detector]
        C --> D[Text Cleaner & Normalizer]
        D --> E[Page-Preserving Overlapping Chunker]
    end

    subgraph Indexing ["2. Vector Retrieval Engine"]
        E --> F[Sentence Transformers: all-MiniLM-L6-v2]
        F --> G[(FAISS Vector Index: IndexFlatIP)]
        G --> H[Fallback Lexical Index: TF-IDF]
    end

    subgraph RAG ["3. Grounded Generation Pipeline"]
        I[User Query] --> J[Vector Similarity Search]
        G --> J
        J --> K{Relevance >= Threshold?}
        K -- No --> L["Fallback: 'I couldn't find sufficient evidence'"]
        K -- Yes --> M[Anti-Injection Prompt Formatter]
        M --> N{Ollama Online?}
        N -- Yes --> O[Ollama llama3.2:3b Local LLM]
        N -- No --> P[Retrieval-Only Evidence Mode]
    end

    subgraph Diffing ["4. Regulatory Comparison Engine"]
        Q[Document A] & R[Document B] --> S[difflib SequenceMatcher]
        S --> T[Modifications: Side-by-Side]
        S --> U[Additions & Removals]
        S --> V[HTML Diff Table]
    end

    subgraph UI ["5. Streamlit Presentation Layer"]
        O & P & L --> W[Ask Documents View + Citations]
        T & U & V --> X[Compare Regulations View]
    end
```

---

## 5. Technology Stack

| Layer | Technology | Rationale / Benefits |
|---|---|---|
| **Web Interface** | Streamlit | Lightweight, interactive dashboard with custom CSS |
| **PDF Extraction** | PyMuPDF (`pymupdf`) | Fast, native C-based extraction preserving page boundaries |
| **Embeddings** | Sentence Transformers (`all-MiniLM-L6-v2`) | Compact (80 MB), fast CPU inference, 384 dimensions |
| **Vector Store** | FAISS (`faiss-cpu`) | High-performance exact Inner Product (Cosine Similarity) |
| **Local LLM** | Ollama (`llama3.2:3b`) | 100% private, zero API cost, runs on CPU/laptop |
| **Diff Engine** | Python standard `difflib` | Reliable sequence matching without heavy dependencies |
| **Automated Testing** | `pytest` | 15 comprehensive unit & integration tests |

---

## 6. Project Folder Structure

```text
Fintech-RAG/
├── app.py                      # Fullstack Streamlit application
├── requirements.txt            # Minimal, verified project dependencies
├── README.md                   # Complete architectural and setup guide
├── .gitignore                  # Excludes .venv, cache, and generated indices
├── data/
│   ├── raw/                    # Uploaded & synthetic sample RBI PDFs
│   │   ├── synthetic_kyc_baseline_2016.pdf
│   │   └── synthetic_kyc_revised_2023.pdf
│   └── processed/              # FAISS indices, chunks, and metadata caches
├── src/
│   ├── __init__.py
│   ├── document_loader.py      # PyMuPDF ingestion & page metadata tracking
│   ├── text_processor.py       # Regulatory text cleaning & clause chunker
│   ├── vector_store.py         # FAISS index, SentenceTransformers & fallback
│   ├── rag_pipeline.py         # Grounded RAG, Ollama client & citation engine
│   └── document_compare.py     # difflib side-by-side diffing & legal disclaimer
└── tests/
    ├── __init__.py
    ├── create_test_fixtures.py # Programmatic synthetic PDF fixture generator
    ├── test_document_loader.py # Ingestion & page extraction tests
    ├── test_text_processor.py  # Text cleaning & chunking tests
    ├── test_document_compare.py# Sequence diffing & modification tests
    ├── test_rag_pipeline.py    # Vector retrieval, grounding & refusal tests
    └── fixtures/               # Labeled synthetic test fixtures
```

---

## 7. Windows PowerShell Installation Instructions

Open PowerShell in the project directory:

```powershell
# 1. Navigate to project root
cd c:\Users\StuDenT.DD.000\Downloads\Fintech-RAG

# 2. Verify installed Python version (Python 3.13 recommended)
py -3.13 --version

# 3. Create virtual environment
py -3.13 -m venv .venv

# 4. Activate virtual environment
.\.venv\Scripts\Activate.ps1

# 5. Install dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 8. Instructions for Running the Application

Ensure the virtual environment is activated:

```powershell
# Start the Streamlit application
.\.venv\Scripts\streamlit.exe run app.py
```

The web dashboard will open automatically in your browser at:
`http://localhost:8501`

---

## 9. Instructions for Loading RBI Documents

1. **Synthetic KYC Baseline & Revised Directions:**
   Pre-loaded automatically in `data/raw/` for instant evaluation.
2. **Uploading Official RBI Documents:**
   - Download the official KYC Master Direction or Circular from the [RBI Master Directions Portal](https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx?did=338).
   - Use the sidebar **"Upload RBI Master Direction / Circular PDF"** file uploader.
   - The application automatically extracts text, chunks pages, and updates the FAISS vector index.

---

## 10. How to Use the Application

### Workflow A: Ask Documents
1. Navigate to the **"🔍 Ask Documents"** tab.
2. Click any of the pre-configured sample question pills (e.g. *Officially Valid Documents (OVD)* or *Periodic KYC update timelines*), or type a custom question.
3. Click **"🔍 Submit Inquiry"**.
4. Inspect the generated answer, latency badge, and expandable **Verifiable Regulatory Citations** showing exact origin pages.
5. Click **"🚫 Test Safe Fallback"** to test how ReguLens safely refuses an unsupported query without hallucinating.

### Workflow B: Compare Documents
1. Navigate to the **"⚖️ Compare Regulations"** tab.
2. Select **Document A** (`synthetic_kyc_baseline_2016.pdf`) and **Document B** (`synthetic_kyc_revised_2023.pdf`).
3. Click **"⚖️ Compare Documents"**.
4. Review:
   - **Overall Textual Similarity Metric** (e.g., 55% similarity).
   - **Modifications Tab:** View original 2016 wording side-by-side with 2023 revised wording.
   - **Additions Tab:** Highlights newly inserted clauses (e.g. Video-CIP live interaction mandates).
   - **Removals Tab:** Deprecated clauses.

---

## 11. Model Setup and Resource Requirements

- **Embedding Model:** `sentence-transformers/all-MiniLM-L6-v2` (~80 MB storage, ~200 MB RAM). Runs on CPU in <15ms per query.
- **Local LLM:** Ollama with `llama3.2:3b` (~2.0 GB storage, ~2.5 GB RAM).
  ```powershell
  # Verify Ollama is running
  ollama list
  # If needed, pull model:
  ollama run llama3.2:3b
  ```
- **Fallback Capability:** If Ollama is paused or not running, ReguLens seamlessly engages **Retrieval-Only Mode**, displaying exact retrieved passages and metadata without interruption.

---

## 12. Automated Test Suite

To run the automated test suite:

```powershell
.\.venv\Scripts\pytest -v tests
```

### Test Results
```text
tests/test_document_compare.py::test_compare_identical_documents PASSED  [  6%]
tests/test_document_compare.py::test_detect_additions_removals_modifications PASSED [ 13%]
tests/test_document_compare.py::test_compare_documents_from_synthetic_pdfs PASSED [ 20%]
tests/test_document_loader.py::test_pdf_extraction_and_page_metadata PASSED [ 26%]
tests/test_document_loader.py::test_empty_pdf_handling PASSED            [ 33%]
tests/test_document_loader.py::test_scanned_image_pdf_ocr_warning PASSED [ 40%]
tests/test_document_loader.py::test_missing_file_handling PASSED         [ 46%]
tests/test_document_loader.py::test_bytesio_stream_loading PASSED        [ 53%]
tests/test_rag_pipeline.py::test_vector_retrieval_finds_relevant_chunk PASSED [ 60%]
tests/test_rag_pipeline.py::test_unsupported_question_insufficient_evidence PASSED [ 66%]
tests/test_rag_pipeline.py::test_rag_retrieval_only_mode PASSED          [ 73%]
tests/test_rag_pipeline.py::test_citation_integrity_and_disclaimer PASSED [ 80%]
tests/test_text_processor.py::test_clean_text_preserves_regulatory_sections PASSED [ 86%]
tests/test_text_processor.py::test_chunk_preserves_page_numbers_and_metadata PASSED [ 93%]
tests/test_text_processor.py::test_chunk_empty_document PASSED           [100%]

============================= 15 passed in 7.70s ==============================
```

---

## 13. Hackathon 5-Question Evaluation & Failure Analysis

| ID | Test Type | Query | Expected & Actual Result | Grounding Status |
|---|---|---|---|---|
| **T1** | Direct Lookup | *"What are the Officially Valid Documents (OVD) for KYC identification?"* | Returns Passport, Driving Licence, Aadhaar proof, Voter ID, NREGA job card from Page 2 | ✅ Grounded (Page 2) |
| **T2** | Specific Rule Detail | *"What is the periodic KYC updation schedule for high risk vs low risk customers?"* | High risk: at least once every 2 years; Low risk: once every 10 years | ✅ Grounded (Page 2) |
| **T3** | Regulatory Evolution | *"What does the revised direction say about Video-based Customer Identification Process (V-CIP)?"* | Identifies Section 4A additions: live interaction, facial matching, geotagging | ✅ Grounded (Page 2) |
| **T4** | Unsupported Query | *"What will RBI announce regarding cryptocurrency capital gains tax next year?"* | Safely outputs: *"I couldn't find sufficient evidence in the selected documents."* | ✅ Safe Refusal |
| **T5** | Document Comparison | *"What wording changed between baseline and revised versions?"* | Detects 4 modifications and 6 additions including V-CIP | ✅ Wording Diff Verified |

### Documented Failure Analysis
1. **Scanned/Raster PDFs:** Older RBI circulars published without digital text layers cannot be extracted via PDF parsers. ReguLens detects low character counts (< 30 chars/page) and flags `ocr_required: True` instead of producing hallucinations.
2. **Akamai WAF on `rbidocs.rbi.org.in`:** Direct automated HTTP downloads to `rbidocs.rbi.org.in` may return HTTP 418 due to bot protection. ReguLens provides interactive drag-and-drop upload in the UI as the robust operational pathway.

---

## 14. Limitations and Responsible-Use Disclaimer

> **IMPORTANT LEGAL DISCLAIMER:**  
> ReguLens is an informational and technological prototype developed for regulatory exploration and comparative analysis. It is **not** an official publication of the Reserve Bank of India and does **not** constitute legal, compliance, or financial advice. Textual differences identified by the system represent wording differences and should not be construed as verified regulatory amendments without independent legal review.

---

## 15. Official RBI Data Sources

- [RBI Master Directions Portal](https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx?did=338)
- [RBI Circulars Index](https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx)
- [RBI Notifications](https://www.rbi.org.in/Scripts/NotificationUser.aspx)
- [RBI KYC Master Direction (Updated)](https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx?id=11566)

---

## 16. User Interface Gallery

| Feature | Interface Layout |
|---|---|
| **Grounded Ask Documents** | Natural language question bar, clickable sample questions, grounded LLM answer card, latency and model badge, expandable verified citations with page numbers. |
| **Compare Regulations** | Side-by-side diff viewer with overall similarity gauge, separate tabs for Modifications, Additions, Removals, and full interactive HTML Sequence table. |
| **Document Repository** | Extracted page viewer, character count metrics, OCR detector warnings, and metadata inspection. |
| **Evaluation Hub** | 5-question benchmark execution table with latency and grounding audit log. |
