# AI-Powered IT Support & Incident Resolution Agent
## System Architecture & Technical Specification

### 1. Executive Summary
The **AI-Powered IT Support & Incident Resolution Agent** is an enterprise-grade AI system designed to resolve employee Tier-1/Tier-2 IT issues, automate troubleshooting with grounded retrieval (RAG), and interact with IT infrastructure using tool calling (agentic workflows). When issues cannot be resolved automatically, it creates structured incident tickets and escalates to human engineers with full conversational context and confidence scoring.

---

### 2. Core Functional Requirements
1. **Intelligent Query Understanding**: Identify intent, entity extractions (error codes, software names, device types), and detect issue urgency.
2. **Context-Grounded Retrieval (RAG)**:
   - Ingest IT policies, troubleshooting manuals, and FAQs (PDF/Markdown).
   - Chunk, index, and retrieve with hybrid search (dense semantic + sparse keyword) and reranking.
   - Strictly answer based on context, suppressing hallucinations.
3. **Historical Incident Matching**:
   - Query past resolved tickets to find proven workarounds for recurring issues (e.g., "Error 809 VPN").
4. **Agentic Tool Execution**:
   - `check_service_status(service_name)`: Verify if upstream services (SSO, VPN, Email, JIRA) are healthy.
   - `check_user_access(user_id, application)`: Validate directory/group permissions.
   - `create_ticket(user_id, category, priority, summary)`: Auto-file tickets in the database.
   - `escalate_ticket(ticket_id, reason)`: Escalate low-confidence or high-severity blockers to human engineers.
5. **Confidence & Hallucination Guardrails**:
   - Calculate retrieval relevance and answer support metrics.
   - If confidence is below threshold (< 0.70), avoid guessing and initiate escalation.
6. **Enterprise Dual-View UI**:
   - **Employee Portal**: Interactive chat, source evidence preview, ticket tracking, and feedback rating (thumbs up/down).
   - **IT Admin Dashboard**: Ticket volume metrics, AI resolution vs. escalation breakdown, response latency, and frequent failure categories.

---

### 3. Non-Functional Requirements
- **Response Latency**: End-to-end response < 3 seconds for direct RAG queries.
- **Security & Privacy**: No hardcoded API keys; all configuration managed via `.env`. Tool permissions strictly sanitized against prompt injection.
- **Modularity**: Swappable LLM providers (Gemini, OpenAI, Anthropic) and storage backends (SQLite, PostgreSQL, ChromaDB).
- **Testability**: Unit and integration test coverage across ingestion, retrieval, agent tools, and API endpoints using `pytest`.

---

### 4. Target Architecture & Data Flow

```
[Employee Query]
       │
       ▼
[FastAPI REST Layer]
       │
       ▼
[Agent Orchestrator] ◄───► [Conversation Memory]
       │
       ├──► [Hybrid Retriever] ──► [ChromaDB + Docs] ──► [Reranker]
       │
       ├──► [Incident DB] ───────► [PostgreSQL / SQLite]
       │
       └──► [Tool Registry] ─────► [Service APIs / Mock Directory]
       │
       ▼
[Prompt Synthesizer + LLM Engine]
       │
       ▼
[Confidence Evaluator + Guardrails]
       │
       ▼
[Grounded Answer + Citations + Action Summary]
```

---

### 5. Project Roadmap (Phases 0 to 25)
- **Phase 0**: Project Planning & System Architecture *(Current)*
- **Phase 1**: Clean Directory Structure & Dependency Setup
- **Phase 2**: Synthetic Enterprise IT Knowledge Base Creation
- **Phase 3**: Document Processing & Semantic Chunking Pipeline
- **Phase 4**: Vector Embeddings & ChromaDB Storage
- **Phase 5**: Basic Grounded RAG Pipeline
- **Phase 6**: Exact Source Citation & Metadata Tracking
- **Phase 7**: Historical Incident Database & Retrieval
- **Phase 8-10**: Agentic Decision-Making, Tool Calling & Support Workflows
- **Phase 11-14**: Confidence Scoring, Memory, Hybrid Retrieval & Reranking
- **Phase 15-17**: FastAPI Backend, Streamlit UI & User Feedback Loop
- **Phase 18-21**: RAGAS Evaluation, Benchmarking, Security & Pytest Suite
- **Phase 22-25**: Deployment, Production GitHub Repository, Resume & Interview Prep
