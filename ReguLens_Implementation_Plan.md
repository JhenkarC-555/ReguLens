# ReguLens — Implementation Plan

**Project title:** ReguLens: Evidence-Based RBI Regulatory Change Intelligence Using RAG

**Objective:** Build a web application that lets users ask questions about RBI regulations, compare related regulatory documents, identify textual changes, and view evidence-backed answers with source references.

This plan is designed for a **3-hour hackathon**, using a small dataset and a free-to-use technology stack.

## 1. Project Scope

### Feature 1 — Ask RBI Documents
Users ask questions in natural language and receive answers grounded in retrieved regulatory passages.

### Feature 2 — Compare Regulations
Compare two related documents or versions and highlight added, removed, and modified text.

### Feature 3 — Evidence and Citations
Show the source document, publication date, page number when available, and relevant passage behind each answer.

### Feature 4 — Safe Fallback
If the selected documents do not support an answer, display:

> I couldn't find sufficient evidence in the selected documents.

**Hackathon boundary:** Do not attempt to build a complete RBI regulatory search engine or production-grade compliance platform in three hours.

## 2. Technology Stack

| Component | Recommended technology | Purpose |
|---|---|---|
| User interface | Streamlit | Chat, document selection, and comparison |
| PDF extraction | PyMuPDF | Extract text and page numbers |
| Text processing | Python | Clean text and split it into chunks |
| Embeddings | Sentence Transformers | Represent passages as vectors |
| Vector retrieval | FAISS | Retrieve relevant passages |
| Generation | Ollama local model or an available free-tier API | Generate grounded answers |
| Comparison | Python `difflib` | Detect textual changes |
| Source tracking | Python data structures or JSON | Preserve document and page metadata |
| Version control | Git and GitHub | Store source code and README |

These tools can be used without paid software licenses, although API access, hosting, and hardware limitations may introduce costs or restrictions. Test model compatibility and memory usage before the event. If local generation is too slow, use a permitted API fallback or demonstrate retrieval and comparison without generation.

## 3. System Architecture

### RAG pipeline

1. **RBI source documents:** PDFs, circulars, and Master Directions.
2. **Document ingestion:** Extract text page by page and preserve metadata.
3. **Preprocessing and chunking:** Clean text and split it into manageable, overlapping passages.
4. **Embedding and indexing:** Create embeddings and store them in FAISS.
5. **Question retrieval:** Retrieve the most relevant passages.
6. **Answer generation:** Send the question and retrieved evidence to an LLM with instructions to answer only from the evidence.
7. **Results:** Display the answer, evidence, source title, date, and page number when available.

### Document-comparison pipeline

1. Select two related documents or versions.
2. Extract and normalize their text.
3. Align corresponding sections where possible.
4. Use Python `difflib` to detect additions, removals, and modified text.
5. Display the differences beside the original text and source details.

Text differences are not automatically legally significant changes. The app should distinguish detected wording changes from verified regulatory implications.

## 4. Data Collection Plan

Start with one regulatory topic to keep the documents relevant to one another.

**Recommended starting topic:** RBI's Know Your Customer (KYC) directions.

Official starting resources:

- [RBI Circular Index](https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx)
- [RBI Master Directions](https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx?did=338)
- [RBI Notifications](https://www.rbi.org.in/Scripts/NotificationUser.aspx)

Collect:

- One suitable consolidated direction.
- One or two related amendment circulars.
- An earlier version of the same direction, if available and clearly identifiable.
- Official publication dates, titles, URLs, and page numbers.

An amendment circular and a consolidated direction are not necessarily directly comparable versions. If two comparable versions are unavailable, demonstrate change detection on clearly selected passages or sections and label the comparison accurately.

### Suggested metadata

| Field | Description |
|---|---|
| Document ID | Unique identifier, e.g. `RBI_KYC_001` |
| Document title | Official title |
| Publication date | Date shown by RBI |
| Document type | Circular or Master Direction |
| Source URL | Original RBI URL |
| Text file | Extracted text filename |
| Page mapping | Mapping from passage to PDF page |

Do not invent missing dates or describe a document as current without checking its status.

## 5. Project Folder Structure

```text
ReguLens/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── raw/
│   │   ├── rbi_document_1.pdf
│   │   └── rbi_document_2.pdf
│   └── processed/
├── src/
│   ├── document_loader.py
│   ├── text_processor.py
│   ├── vector_store.py
│   ├── rag_pipeline.py
│   └── document_compare.py
├── tests/
│   └── test_comparison.py
└── .gitignore
```

Keep downloaded PDFs, extracted text, the vector index, and metadata organized. Avoid committing large or unnecessary generated files to GitHub.

## 6. Implementation Sequence

### Step 1 — Build the document loader
Implement `document_loader.py` using PyMuPDF. Extract text page by page, remove unnecessary whitespace, and preserve page numbers.

**Success criterion:** Extracted text is readable and every passage can be traced to a PDF page.

### Step 2 — Create the retrieval index
Implement `text_processor.py` and `vector_store.py`. Split text into chunks of roughly 400–700 tokens with modest overlap, embed each chunk, and store its vector with source metadata.

**Success criterion:** A test query returns relevant passages with correct source details.

### Step 3 — Implement the RAG pipeline
In `rag_pipeline.py`, retrieve the top few passages and pass them to the LLM with a prompt requiring evidence-based answers.

**Success criterion:** Answers are supported by retrieved text, and insufficient evidence produces a clear fallback.

### Step 4 — Implement document comparison
In `document_compare.py`, normalize whitespace and compare text with Python's `difflib`. Display added, removed, and modified passages separately.

**Success criterion:** A deliberately modified sample paragraph produces the expected differences.

### Step 5 — Build the Streamlit interface
Create two main sections: **Ask Documents** and **Compare Documents**. Display citations alongside answers and let users open the original source.

**Success criterion:** A user can complete both workflows without using the terminal.

### Step 6 — Test and prepare the demo
Test supported questions, unsupported questions, citations, and comparison output. Record known limitations in the README.

**Success criterion:** Five prepared questions work reliably, including one that should return the insufficient-evidence response.

## 7. Three-Hour Schedule

| Time | Task |
|---|---|
| 0:00–0:25 | Select and download the documents |
| 0:25–1:00 | Extract text, chunk, and index |
| 1:00–1:45 | Implement RAG and citations |
| 1:45–2:20 | Add document comparison |
| 2:20–2:45 | Test questions and failure cases |
| 2:45–3:00 | Prepare the demo and README |

Prioritize a working end-to-end question-answering workflow before polishing the comparison feature.

## 8. User Interface Design

Build a simple dashboard with two main sections.

### Ask Documents
- Question input.
- Answer generated from retrieved evidence.
- Supporting passages.
- Source document title, date, page, and official link when available.

### Compare Documents
- Select the two documents.
- Display **Added**, **Removed**, and **Modified** text separately.
- Keep original wording visible so users can verify the detected changes.

## 9. Testing Plan

Prepare these five test questions before the demonstration.

| Test | Example | Expected result |
|---|---|---|
| Direct lookup | “What does the selected document say about KYC requirements?” | Relevant passage and citation |
| Specific detail | “Which section discusses this requirement?” | Section or page reference when available |
| Comparison | “What wording changed between these versions?” | Added, removed, or modified text |
| Unsupported question | “What will RBI announce next year?” | Insufficient-evidence response |
| Outdated or conflicting material | Ask about a rule whose status differs between the selected documents | Distinguish document dates and avoid claiming current validity without verification |

If time permits, also test an empty PDF, an image-only scanned PDF, and a document with no relevant passage.

## 10. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Poor PDF extraction | Inspect extracted text before indexing; use OCR only if necessary |
| Local model runs slowly | Test in advance; use a permitted API fallback |
| Incorrect citations | Store page metadata during ingestion and retrieve it with every chunk |
| Misleading change detection | Compare related versions and label textual changes separately from regulatory implications |
| Hallucinated answers | Require source-grounded answers and use a conservative fallback |
| Scope becomes too large | Restrict the prototype to one topic and two or three documents |

## 11. Definition of Done

- [ ] At least two relevant RBI source documents collected.
- [ ] PDF text extracted with source metadata.
- [ ] Vector retrieval returns relevant passages.
- [ ] RAG answers include traceable citations.
- [ ] Unsupported questions receive a fallback.
- [ ] Document comparison identifies sample text changes.
- [ ] Streamlit interface runs locally.
- [ ] Five test questions completed.
- [ ] README includes setup steps, sources, and limitations.

## 12. Final Execution Strategy

Build and verify one complete workflow first:

1. Load one RBI PDF.
2. Ask one question.
3. Retrieve a relevant passage.
4. Generate an answer with its citation.
5. Add document comparison once the question-answering workflow works.

This ensures that a demonstrable RAG prototype exists even if the comparison feature takes longer than expected.

## 13. Important Limitations

- ReguLens is a prototype for regulatory-document exploration, not a substitute for official RBI publications or professional compliance advice.
- Retrieved text may be incomplete or incorrectly extracted from complex PDFs.
- Text differences do not automatically establish legal or operational significance.
- Document status and effective dates must be verified against official sources.
- Do not claim comprehensive regulatory coverage based on a small sample.

## References

- [RBI Circular Index](https://www.rbi.org.in/scripts/BS_CircularIndexDisplay.aspx)
- [RBI Master Directions](https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx?did=338)
- [RBI Notifications](https://www.rbi.org.in/Scripts/NotificationUser.aspx)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [FAISS Documentation](https://faiss.ai/)
- [Sentence Transformers Documentation](https://www.sbert.net/)
- [Python `difflib` Documentation](https://docs.python.org/3/library/difflib.html)
