# NexaSupport AI 🛡️

> **AI-Powered IT Support & Incident Resolution Agent**  
> An enterprise-grade system using LLM + RAG + Agentic AI + Tool Calling to resolve employee IT issues automatically.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/nexasupport-ai.git
cd nexasupport-ai
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 5. Run the backend (Terminal 1)
```bash
uvicorn app.main:app --reload
# API available at: http://localhost:8000
# Swagger docs at: http://localhost:8000/docs
```

### 6. Run the frontend (Terminal 2)
```bash
streamlit run frontend/streamlit_app.py
# UI available at: http://localhost:8501
```

---

## 🏗️ Architecture

```
Employee Query → FastAPI Backend → AI Agent Orchestrator
                                        ↓
                    ┌───────────────────┴────────────────────┐
                    │                                        │
              Hybrid RAG Engine                    Enterprise Tools
              (ChromaDB + BM25)                  (Service Status,
              Incident DB Search                  Ticket Create,
              Reranking Layer                     User Access Check)
                    │                                        │
                    └───────────────┬────────────────────────┘
                                    ↓
                             LLM Engine (Gemini)
                                    ↓
                    Grounded Answer + Sources + Confidence
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM** | Google Gemini 1.5 Flash |
| **RAG** | LangChain + ChromaDB |
| **Embeddings** | Sentence Transformers / Gemini |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | Streamlit |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Evaluation** | RAGAS |
| **Testing** | pytest |

---

## 📁 Project Structure

```
nexasupport-ai/
├── app/
│   ├── main.py           ← FastAPI entry point
│   ├── config.py         ← Environment configuration
│   ├── api/              ← API route handlers
│   ├── agents/           ← AI agent orchestrator
│   ├── rag/              ← Retrieval pipeline
│   ├── tools/            ← Tool calling functions
│   ├── database/         ← DB models & sessions
│   ├── models/           ← Pydantic schemas
│   ├── services/         ← Business logic
│   └── utils/            ← Shared utilities
├── frontend/
│   └── streamlit_app.py  ← Streamlit UI
├── data/
│   ├── documents/        ← Raw IT knowledge base docs
│   ├── processed/        ← Chunked text output
│   └── tickets/          ← Exported ticket data
├── tests/                ← pytest test suite
├── evaluation/           ← RAGAS evaluation scripts
├── docs/                 ← Architecture & specs
├── .env.example          ← Environment variable template
├── requirements.txt
└── README.md
```

---

## ⚙️ Environment Variables

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | `gemini` or `openai` | `gemini` |
| `GEMINI_API_KEY` | Google AI Studio API key | *(required)* |
| `EMBEDDING_PROVIDER` | `local` or `gemini` | `local` |
| `CONFIDENCE_THRESHOLD` | Min confidence before escalation | `0.70` |
| `DATABASE_URL` | SQLite or PostgreSQL connection string | SQLite |

---

## 📊 Build Status

| Phase | Status | Key Files |
|---|---|---|
| Phase 0 — Project Planning | ✅ Complete | `docs/PROJECT_SPEC.md` |
| Phase 1 — Project Setup | ✅ Complete | `app/main.py`, `app/config.py` |
| Phase 2 — IT Knowledge Base | ✅ Complete | `data/documents/*.md` (7 docs) |
| Phase 3 — Document Processing | ✅ Complete | `app/utils/document_loader.py`, `text_chunker.py`, `scripts/ingest_documents.py` |
| Phase 4 — Embeddings + ChromaDB | ✅ Complete | `app/rag/embeddings.py`, `vector_store.py`, `scripts/build_index.py` |
| Phase 5 — Basic RAG Pipeline | ✅ Complete | `app/rag/retriever.py`, `prompt_builder.py`, `llm_client.py`, `pipeline.py` |
| Phase 6 — Source Citations + API | ✅ Complete | `app/models/schemas.py`, `app/api/chat.py` |
| Phase 7 — Incident Database | ✅ Complete | `app/database/`, `app/services/ticket_service.py`, `app/api/tickets.py` |
| Phase 8 — Agentic Orchestrator | ✅ Complete | `app/agents/support_agent.py` — 4 parallel tool calls |
| Phase 9 — Tool Calling Suite | ✅ Complete | `app/tools/it_tools.py` — KB search, ticket search, service status, user access, create ticket |
| Phase 10 — Domain Workflows | ✅ Complete | `app/agents/workflows.py` — VPN outage & account lockout flows |
| Phase 11 — Confidence Guardrails | ✅ Complete | `app/agents/guardrails.py` — multi-signal hallucination prevention |
| Phase 12 — Conversation Memory | ✅ Complete | `app/agents/memory.py` — multi-turn query reformulation |
| Phase 13 — Hybrid Retrieval + Reranking | ✅ Complete | `app/rag/hybrid_retriever.py` — BM25 + semantic RRF reranking |
| Phase 14 — Auto-Escalation + Ticket Creation | ✅ Complete | `support_agent.py` — auto-creates ticket on low confidence, appends ticket ID to response |
| Phase 15 — Unit Test Suite | ✅ Complete | `tests/test_agent.py`, `tests/test_tools.py`, `tests/test_api.py`, `tests/test_chunker.py` |
| Phase 16 — RAG Evaluation Suite | ✅ Complete | `evaluation/evaluate_rag.py`, `evaluation/golden_dataset.json` (10 Q&A pairs) |

---

*Built as a portfolio AI engineering project demonstrating RAG, Agentic AI, and enterprise LLM patterns.*
