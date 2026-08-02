# Revenue Intelligence Assistant

An AI assistant for Revenue/SaaS analytics: a RAG chat over a self-written
knowledge base of metrics, tool calling for calculations and financial-statement
analysis, CSV/Excel analysis, a live metrics dashboard, a bilingual interface
(EN/UK), and a built-in retrieval-quality evaluation.

**Live demo:** https://revenue-ai-assistant.vercel.app
**Backend API docs:** `https://<your-backend>.onrender.com/docs` — fill in before the review

---

## Architecture

```mermaid
flowchart TD
    User([User]) --> FE[Next.js<br/>Frontend — Vercel]
    FE -->|REST API| BE[FastAPI<br/>Backend — Render]

    subgraph Backend
        BE --> RAG[rag/ — orchestration<br/>+ tool calling loop]
        BE --> TOOLS[tools/ — 8 LangChain tools]
        BE --> LOAD[loaders/ — DataSource<br/>CSV / Stripe]
        BE --> MET[metrics/ — RevenueMetricsEngine]
        BE --> MON[monitoring/ — request logging]
        BE --> EVAL[evaluation/ — retrieval benchmark]
    end

    RAG --> VDB[(ChromaDB<br/>vector store)]
    RAG --> LLM[OpenRouter<br/>LLM API]
    VDB --> EMB[HuggingFace<br/>Inference API — embeddings]
    LOAD --> CSV[(CSV data)]
    LOAD --> STRIPE[(Stripe API<br/>test mode)]

    KB[knowledge_base/<br/>metrics · frameworks · sql<br/>industry_references<br/>EN + UK] -.ingest.py.-> VDB
```

Frontend and backend are independent services that only talk over a REST
API. The backend knows nothing about React/Next.js; the frontend knows
nothing about LangChain/Chroma. The data source for live metrics plugs
in through a `DataSource` abstraction — swapping CSV for Stripe requires
no changes to the rest of the code.

---

## Why RAG instead of fine-tuning?

The project's knowledge (metric definitions, SQL templates, industry
benchmarks) is **dynamic reference content**, not stable language
behavior:

- **Updatable without retraining** — a new metric is a `.md` file +
  `python ingest.py`, not a model rebuild.
- **Transparency** — every answer returns its `sources`, so a claim can
  be traced back to a document. A fine-tuned model can't do this.
- **Protection against stale numbers** — `industry_references/`
  deliberately holds no specific benchmark figures (they go stale every
  year); RAG lets the system point at a source instead of baking a
  number into the weights.
- **Right problem for the size of the task** — the core challenge here is
  correct retrieval and calling the right tool, not teaching the model a
  new "voice" — a base LLM with good context is already good enough at
  that.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| Backend | FastAPI, LangChain, ChromaDB |
| LLM | OpenRouter (OpenAI-compatible API) |
| Embeddings | HuggingFace Inference API (remote, no torch — light runtime) |
| Data | pandas, Stripe API (optional), SQLite (logs) |
| Testing | pytest (45 test cases) |
| Deployment | Vercel (frontend) + Render (backend) |

---

## Key features

- **RAG** — retrieval across 20+ documents (metrics, frameworks, sql,
  industry_references), EN + UK, chunking + similarity search via Chroma
- **Tool calling** — 8 tools: `calculate_kpi`, `generate_sql`,
  `get_benchmark`, `get_csv_agent`, `csv_aggregate`, `csv_row_sum`,
  `analyze_financial_statement`, `get_live_metric`
- **CSV/Excel Analyzer** — exact aggregations via pandas (not LLM
  hallucinations for numbers), plus dedicated parsing for uploaded
  Balance Sheet / Income Statement / Cash Flow files (line lookup, year
  comparison, YoY growth, total validation)
- **KPI Calculator** — a form with fields specific to each metric
- **Multi-language** — UI, LLM answers, and the knowledge base itself in
  EN/UK
- **Live Metrics** — a separate data layer (not RAG): a `DataSource`
  abstraction (CSV/Stripe) → `RevenueMetricsEngine` → a live snapshot,
  refreshed via Vercel Cron
- **Security** — prompt injection guard (on user text **and** on
  uploaded file content), input sanitization, API key validation
- **Logging & Monitoring** — every request is logged (latency, tools
  used, errors) to SQLite, with a dedicated admin panel
- **RAG Evaluation** — a custom retrieval benchmark, runnable from a
  script or from the UI (measures Top-K accuracy, not just "does the
  answer feel good")

---

## RAG Evaluation — results

Latest run (24 questions covering every knowledge base document):

| Metric | Value |
|---|---|
| **Top-1 Accuracy** | 87.5% |
| **Top-3 Accuracy** | 100% |
| **Avg Retrieval Time** | ~200 ms |

Run it: `python -m evaluation.run_evaluation`, or from the UI —
Admin → Run Evaluation.

---

## Running locally

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in OPENROUTER_API_KEY, HF_TOKEN, REFRESH_TOKEN
python ingest.py
python -m metrics.snapshot_service
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:3000`.

### Tests

```bash
cd backend
pytest tests/ -v
```

---

## Deployment

**Backend → Render**
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt && python ingest.py && python -m metrics.snapshot_service`
- Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- Env vars: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `HF_TOKEN`, `REFRESH_TOKEN`,
  `FRONTEND_ORIGIN`, `DATA_SOURCE`

**Frontend → Vercel**
- Root Directory: `frontend`
- Env vars: `NEXT_PUBLIC_API_URL`, `BACKEND_URL`, `REFRESH_TOKEN`

---

## Project structure

```
backend/
├── api/              — FastAPI routes
├── rag/               — retrieval + tool-calling orchestration
├── tools/             — 8 LangChain tools, split by domain:
│   ├── analytics_tools.py     — re-exports the tools below (stable import path)
│   ├── csv_io.py               — shared CSV loading helper
│   ├── csv_tools.py            — csv_aggregate, csv_row_sum, get_csv_agent
│   ├── kpi.py                  — calculate_kpi, get_benchmark, get_live_metric
│   ├── sql.py                  — generate_sql
│   └── financial_statement.py  — analyze_financial_statement + parsing helpers
├── loaders/           — DataSource: CsvLoader, StripeSnapshotLoader
├── metrics/           — RevenueMetricsEngine, snapshot_service
├── monitoring/        — request logging (SQLite)
├── evaluation/        — RAG retrieval evaluation
├── tests/             — pytest suite
├── scripts/           — standalone maintenance tools (seed data)
├── knowledge_base/    — RAG documents (EN)
└── knowledge_base_uk/ — RAG documents (UK)

frontend/
└── src/
    ├── app/           — Next.js pages
    ├── components/    — Chat, CSV, KPI, Admin views
    └── lib/           — API client, i18n strings
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | API key status check |
| POST | `/api/chat` | RAG chat with tool calling |
| POST | `/api/upload-csv` | Upload a CSV/Excel file |
| POST | `/api/csv-chat` | Ask a question about the uploaded file |
| POST | `/api/kpi` | KPI calculation + benchmark |
| GET | `/api/kpi-metrics` | List of supported metrics |
| GET | `/api/live-metrics` | Current live snapshot |
| POST | `/api/live-metrics/refresh` | Recompute live metrics (protected) |
| GET | `/api/admin/logs` | Request logs (protected) |
| GET | `/api/admin/stats` | Aggregate monitoring stats (protected) |
| POST | `/api/admin/evaluate` | Run RAG evaluation (protected) |

---

## About the knowledge base

The knowledge base is synthesized in my own words from well-known SaaS
concepts and publicly available documentation (Stripe, HubSpot,
ProfitWell, OpenView, Bessemer, Winning by Design) — without verbatim
copying. `industry_references/` deliberately contains **no** specific
numeric benchmarks, only a description of what each source publishes —
see "Why RAG instead of fine-tuning?" above.

---

## Known limitations

- Retrieval is single-pass dense similarity search — no query
  rewriting/multi-query and no hybrid (keyword + vector) search yet
- No multi-model support in the UI (the model is set via an env var)
- No token usage / cost tracking
- `logs.db` and in-memory uploaded-file registry reset on every redeploy
  on Render's free tier
- `get_csv_agent` uses `allow_dangerous_code=True` (LangChain) — an
  acceptable trade-off for a course project in an isolated container, but
  not for production with untrusted traffic without a real sandbox

---

## Context

A learning project (Turing College, AI Engineering Sprint 2: LangChain,
RAG, Streamlit/Next.js). Optional tasks completed: **multi-language
support** and **RAG evaluation** (Hard), **prompt injection protection**
and **logging and monitoring** (Medium).
