# DOCMind Enterprise 🤖📄

> A startup-grade, production-quality AI Document Intelligence Platform built with clean architecture using Next.js (App Router), FastAPI, PostgreSQL, Redis, ChromaDB, and NVIDIA NIM endpoints.

DOCMind Enterprise is a modular, high-performance RAG (Retrieval-Augmented Generation) document intelligence platform that allows enterprises to upload PDFs, manage directory structures, index contents automatically, ask conversational questions with live streaming sources/citations, and extract deep document analysis (executive summary, risks, deadlines, milestones, and entity maps) using cloud-hosted LLM endpoints.

---

## 🌟 Key Features

- **Advanced Retrieval-Augmented Generation (RAG) Pipeline**:
  - **Multi-Query Expansion**: Rewrites user queries into alternative formulations to expand semantic coverage.
  - **Hybrid Search**: Merges dense semantic embeddings (MMR Chroma vector store) with sparse keyword matching (BM25 file indexer).
  - **Reciprocal Rank Fusion (RRF)**: Integrates dense and sparse results into a single rank list using standard weighting constants.
  - **Cross-Encoder Re-ranking**: Re-evaluates retrieved chunks using a cross-encoder model to return the most relevant candidates.
  - **Parent Document Retrieval**: Child chunks (400 characters) are mapped for high granularity, but full parent pages (page text context) are injected into the LLM context to prevent loss of information.
- **Premium SaaS Frontend UI (Next.js, TypeScript, Tailwind CSS)**:
  - Vercel-style dark glassmorphism design system.
  - Interactive file explorer supporting nested folders, document checklists, renaming, and deletion.
  - Streamlit-like conversational workspace featuring citations highlighting, query latency accordions, markdown rendering, code formatting, and suggestion prompts.
  - Slide-out Document Intelligence sidebar displaying Executive Summary, Obligations, Deadlines, Risks, and Named Entities.
- **Robust Observability**:
  - Structured JSON logs for microservice log aggregators.
  - Prometheus metrics scraper endpoint (`/metrics`) monitoring latencies, request rates, and token counts.
- **Microservices Orchestration (Docker Compose)**:
  - Spin up Next.js frontend, FastAPI backend, PostgreSQL, Redis, and ChromaDB with a single command.

---

## 🛠️ Project Directory Tree

```text
pdf_qa_chatbot/
├── backend/
│   ├── app/
│   │   ├── ai/             # Advanced RAG Pipeline (pipeline.py)
│   │   ├── api/            # API Router endpoints (Auth, Documents, Chat, Admin)
│   │   ├── core/           # Config settings, JWT operations, Prometheus metrics
│   │   ├── db/             # SQLAlchemy schemas (models.py) and sessions
│   │   ├── repositories/   # DB query abstraction (User, Document, Folder, Chat)
│   │   └── services/       # Business logic layer (Auth, Chat, Document, Storage)
│   ├── tests/              # pytest unit & integration test suites
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js pages, layouts, and global Tailwind CSS style
│   │   ├── lib/            # Axios API fetching client with auto-refresh tokens
│   │   └── types/          # TypeScript interfaces
│   ├── Dockerfile
│   └── package.json
├── sample_documents/       # Tracked public sample documents for testing
├── docker-compose.yml      # Multi-container cluster orchestration
├── .gitignore              # Ignores runtime databases, local uploads, and secrets
└── README.md
```

---

## ⚙️ Installation & Run

### Prerequisites
- Docker & Docker Compose
- An NVIDIA NIM API Key (or OpenAI/Ollama settings override)

### 1. Configure Environment
Copy the example environment settings to `.env` inside the `backend/` directory:
```bash
cp backend/.env.example backend/.env
```
Open `backend/.env` and insert your API key:
```text
NVIDIA_API_KEY=nvapi-your-nvidia-key
```

### 2. Launch with Docker Compose
Run the entire platform on localhost:
```bash
docker-compose up --build
```

### 3. Localhost Endpoint Directory

Once running, access the services:
- **Frontend Panel**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Backend Root**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Prometheus Metrics Scraper**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
- **ChromaDB API Instance**: [http://localhost:8001](http://localhost:8001)

---

## 📄 Sample Documents

To make it as easy as possible for contributors to clone and test DOCMind Enterprise without finding their own files, we have checked public testing files into the [`sample_documents/`](./sample_documents/) directory:
- **`contract_sample.pdf`**: Best for verifying key obligations, risk flags, and timeline deadlines.
- **`resume_sample.pdf`**: Best for testing job experience chronologies and technical skill keywords.
- **`invoice_sample.pdf`**: Best for validating table parsing, billing totals, and financial figures.
- **`research_paper_sample.pdf`**: Best for verifying academic citations, technical self-attention explanations, and hybrid RAG search queries.

*Note: Uploaded documents and private fixtures (`uploads/`, `private_documents/`, etc.) are matched by `.gitignore` and will never be tracked or committed to GitHub.*
