"""FastAPI backend for the Revenue AI Assistant.

Wraps the existing LangChain / RAG / tool-calling logic (unchanged) behind a
REST API so a separate Next.js frontend can talk to it.
"""

import json
import os
import tempfile
import uuid
from typing import Literal, Optional

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from monitoring.logger import recent_logs, summary_stats, track_request
from rag.rag_core import (
    get_llm,
    get_vectorstore,
    has_prompt_injection,
    run_chat_with_tools,
    sanitize_user_input,
    validate_api_key,
)
from tools.analytics_tools import calculate_kpi, get_benchmark

load_dotenv()

app = FastAPI(title="Revenue AI Assistant API")

# CORS: allow the Next.js frontend (set FRONTEND_ORIGIN in .env for production,
# e.g. https://your-app.vercel.app). "*" is fine for local dev only.
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc: Exception):
    """Safety net: an uncaught exception from Starlette's default error path
    can skip CORSMiddleware entirely, which the browser reports as a CORS
    error even though the real problem is a server-side 500. Catching it here
    keeps the response inside FastAPI's normal flow, so CORSMiddleware still
    attaches the right headers.
    """
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=500,
        content={"detail": f"Unhandled server error: {exc}"},
    )

# In-memory registry of uploaded CSVs for this process (fine for a course project;
# use Redis/S3 if this ever needs to survive a restart or run multi-instance).
_UPLOADED_FILES: dict[str, dict] = {}

Lang = Literal["en", "uk"]


class ChatRequest(BaseModel):
    query: str
    lang: Lang = "en"


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
    retrieval_note: Optional[str] = None


class CsvChatRequest(BaseModel):
    file_id: str
    query: str
    lang: Lang = "en"


class KpiRequest(BaseModel):
    kpi_name: str
    value_a: float
    value_b: float
    value_c: Optional[float] = None
    lang: Lang = "en"


@app.get("/api/health")
def health():
    key_ok, key_msg = validate_api_key()
    return {"status": "ok", "api_key_valid": key_ok, "api_key_message": key_msg}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    key_ok, key_msg = validate_api_key()
    if not key_ok:
        raise HTTPException(status_code=400, detail=key_msg)
    if has_prompt_injection(req.query):
        raise HTTPException(status_code=400, detail="prompt_injection_detected")

    safe_query = sanitize_user_input(req.query)
    db = get_vectorstore()
    docs = db.similarity_search(safe_query, k=3, filter={"lang": req.lang})
    note = None
    if not docs:
        # Filtered retrieval found nothing — most likely chroma_db is empty or
        # predates the "lang" metadata field. Retry without the filter so the
        # user still sees *something* was retrieved, and surface a clear note
        # instead of silently returning zero sources.
        docs = db.similarity_search(safe_query, k=3)
        if docs:
            note = (
                f"No '{req.lang}' chunks found (index may need 'python ingest.py' "
                f"to pick up the language metadata) — showing unfiltered results instead."
            )
        else:
            note = "No chunks retrieved at all — check that chroma_db was built (run ingest.py)."
    context = "\n".join(d.page_content for d in docs) if docs else ""

    llm = get_llm()
    with track_request("chat", req.lang, req.query) as log_ctx:
        answer, tools_used = run_chat_with_tools(llm, context, safe_query, lang=req.lang)
        log_ctx["tools_used"] = tools_used

    return ChatResponse(
        answer=answer,
        sources=[doc.metadata for doc in docs],
        retrieval_note=note,
    )


@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    raw = await file.read()
    filename = (file.filename or "").lower()
    is_excel = filename.endswith(".xlsx") or filename.endswith(".xls")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=(".xlsx" if is_excel else ".csv")) as tmp:
            tmp.write(raw)
            raw_path = tmp.name

        try:
            df = pd.read_excel(raw_path) if is_excel else pd.read_csv(raw_path)
            # Normalize column names to plain strings once, right here — otherwise
            # Timestamp/date column headers get serialized differently in the
            # "columns" list vs. the "preview" rows further down, and the
            # frontend can't match them up (looks like every cell is "undefined").
            df.columns = [
                c.isoformat() if hasattr(c, "isoformat") else str(c) for c in df.columns
            ]
        except Exception as exc:  # noqa: BLE001
            kind = "Excel" if is_excel else "CSV"
            raise HTTPException(status_code=400, detail=f"Could not parse {kind} file: {exc}")

        if is_excel:
            # Downstream tools (csv_aggregate, get_csv_agent) read the stored path
            # with pd.read_csv — re-persist as CSV so they don't need to know the
            # original file was Excel.
            csv_path = raw_path.rsplit(".", 1)[0] + ".csv"
            df.to_csv(csv_path, index=False)
        else:
            csv_path = raw_path

        file_id = str(uuid.uuid4())
        _UPLOADED_FILES[file_id] = {"path": csv_path, "columns": list(df.columns), "rows": len(df)}

        return {
            "file_id": file_id,
            "rows": len(df),
            "columns": list(df.columns),
            "preview": json.loads(df.head(5).to_json(orient="records", date_format="iso")),
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 — never let an unhandled error skip CORS headers
        raise HTTPException(status_code=500, detail=f"Unexpected error processing upload: {exc}")


@app.post("/api/csv-chat", response_model=ChatResponse)
def csv_chat(req: CsvChatRequest):
    meta = _UPLOADED_FILES.get(req.file_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Unknown file_id — upload the CSV again.")

    key_ok, key_msg = validate_api_key()
    if not key_ok:
        raise HTTPException(status_code=400, detail=key_msg)
    if has_prompt_injection(req.query):
        raise HTTPException(status_code=400, detail="prompt_injection_detected")

    safe_query = sanitize_user_input(req.query)
    context = f"""
CSV uploaded.

Real file path:
{meta['path']}

Columns:
{", ".join(meta['columns'])}

Rows:
{meta['rows']}

When using get_csv_agent, csv_aggregate, csv_row_sum, or analyze_financial_statement, use the exact file path above.
"""
    llm = get_llm()
    with track_request("csv_chat", req.lang, req.query) as log_ctx:
        answer, tools_used = run_chat_with_tools(
            llm, context, safe_query, allow_any_csv_topic=True, lang=req.lang
        )
        log_ctx["tools_used"] = tools_used

    return ChatResponse(
        answer=answer,
        sources=[{"type": "csv", "rows": meta["rows"], "columns": meta["columns"]}],
    )


@app.post("/api/kpi")
def kpi(req: KpiRequest):
    with track_request("kpi", req.lang, req.kpi_name) as log_ctx:
        result = calculate_kpi.invoke({
            "kpi_name": req.kpi_name,
            "value_a": req.value_a,
            "value_b": req.value_b,
            "value_c": req.value_c,
            "lang": req.lang,
        })
        benchmark = get_benchmark.invoke({"metric_name": req.kpi_name, "lang": req.lang})
        log_ctx["tools_used"] = ["calculate_kpi", "get_benchmark"]
    return {"metric": req.kpi_name, "result": result, "benchmark": benchmark}


@app.get("/api/kpi-metrics")
def kpi_metrics():
    """List of supported KPI names — lets the frontend build the dropdown without hardcoding it twice."""
    return {
        "metrics": ["mrr", "arr", "cac", "ltv", "churn", "nrr", "grr", "payback", "arpu", "ltv_cac"]
    }


@app.get("/api/live-metrics")
def live_metrics():
    """Public read of the latest computed snapshot — used by the frontend dashboard card."""
    from metrics.snapshot_service import read_snapshot

    snap = read_snapshot()
    if not snap:
        raise HTTPException(status_code=404, detail="No live metrics snapshot yet. Trigger a refresh first.")
    return snap


@app.post("/api/live-metrics/refresh")
def trigger_refresh(x_refresh_token: str = Header(default="")):
    """Recomputes the live metrics snapshot from the data source.

    Called by a scheduled job (Render Cron / Vercel Cron hitting this URL), not
    by the frontend directly. Protected by a shared secret so randoms can't
    trigger recomputation.
    """
    expected = os.getenv("REFRESH_TOKEN")
    if not expected or x_refresh_token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing refresh token.")

    from metrics.snapshot_service import refresh

    try:
        snap = refresh()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Refresh failed: {exc}")
    return snap


def _check_admin_token(token: str):
    expected = os.getenv("ADMIN_TOKEN") or os.getenv("REFRESH_TOKEN")
    if not expected or token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing admin token.")


@app.get("/api/admin/logs")
def admin_logs(x_admin_token: str = Header(default=""), limit: int = 100):
    """Recent request logs — endpoint, latency, tools used, errors. Protected."""
    _check_admin_token(x_admin_token)
    return {"logs": recent_logs(limit=limit)}


@app.get("/api/admin/stats")
def admin_stats(x_admin_token: str = Header(default="")):
    """Aggregate monitoring stats: request counts, error rate, avg latency,
    breakdown by endpoint and by which tools fired most often."""
    _check_admin_token(x_admin_token)
    return summary_stats()


@app.post("/api/admin/evaluate")
def admin_evaluate(x_admin_token: str = Header(default=""), lang: str = "en"):
    """Runs the RAG retrieval evaluation (Top-1/Top-3 accuracy, avg latency)
    against evaluation/questions.json and returns the full report. Lets you
    demo retrieval quality live from the deployed site, not just locally."""
    _check_admin_token(x_admin_token)

    from evaluation.run_evaluation import run_evaluation

    try:
        return run_evaluation(lang=lang)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {exc}")
