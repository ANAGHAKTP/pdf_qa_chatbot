# DOCMind Enterprise - Test & Demo Documents

This folder contains public, open-source sample PDF documents intended for testing the advanced RAG pipeline and Document Intelligence features. 

Contributors and developers can immediately upload these files to DOCMind Enterprise to verify parsing, indexing, semantic query retrieval, and structured information extraction.

---

## Sample Documents Directory

### 1. `contract_sample.pdf`
- **What it Demonstrates**: A corporate services agreement detailing legal clauses, warranties, liabilities, and multi-party signatures.
- **Useful For**: Testing the Document Intelligence **Risks & Liabilities** isolation card, contract compliance timeline mapping, and action item checks.
- **Suggested Questions**:
  - *"What are the liability limits and warranty conditions in this contract?"*
  - *"List the termination clauses and notice period requirements."*
  - *"Is there an indemnity clause? Extract its key terms."*

### 2. `resume_sample.pdf`
- **What it Demonstrates**: A professional candidate curriculum vitae showing work history, educational achievements, technical skill matrices, and certifications.
- **Useful For**: Testing **Timeline Extraction**, keyword profile filtering, and candidate qualification entity listings.
- **Suggested Questions**:
  - *"Provide a chronological summary of this candidate's employment timeline."*
  - *"Isolate all technical skills and matching programming languages."*
  - *"What is the candidate's highest educational degree?"*

### 3. `invoice_sample.pdf`
- **What it Demonstrates**: A standard business purchase order / invoice containing billing items, unit prices, tax percentages, payment terms, and vendor names.
- **Useful For**: Testing **Table Parsing**, financial sum extraction, billing metadata isolation, and entity listings.
- **Suggested Questions**:
  - *"What is the invoice number, date, and total balance due?"*
  - *"List the billing items and unit prices in a clean markdown table."*
  - *"Extract the payment terms and bank deposit routing details."*

### 4. `research_paper_sample.pdf`
- **What it Demonstrates**: The seminal research paper *"Attention Is All You Need"* introducing the Transformer architecture. It includes math equations, figures, references, and complex academic explanations.
- **Useful For**: Testing **Parent-Child Retrieval**, sparse/dense hybrid search (BM25 vs Vector embeddings), re-ranking with cross-encoders, and technical glossaries.
- **Suggested Questions**:
  - *"Explain the multi-head self-attention mechanism in simple terms."*
  - *"What are the key advantages of Transformers over recurrent networks (LSTMs)?"*
  - *"Isolate the experimental results and parameters used for the English-to-German translation task."*

---

## Workspace Rules for Demo Documents
- **Public Samples**: Place all public, non-sensitive testing PDFs directly inside this `sample_documents/` directory. These files are tracked by Git.
- **Private Data**: To test the platform with private or sensitive PDFs, place them in a folder matching `sample_documents/private/` or `private_documents/`. These paths are matched by `.gitignore` and will never be tracked or committed to GitHub.
