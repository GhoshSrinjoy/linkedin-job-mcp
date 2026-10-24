"""FastAPI app: JSON API plus the dashboard (static files).

Start:  uvicorn ghostradar.main:app --reload   then open http://127.0.0.1:8000
"""
from __future__ import annotations

import asyncio
import contextlib
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__, db, services, tasks
from .ml import model as ml_model
from . import prefs as user_prefs
from .analysis import baselines
from .config import settings
from .http import PoliteClient
from .models import (
    AuditIn,
    EventIn,
    NotesImport,
    PrefsIn,
    CaptureIn,
    CheckRequest,
    CheckResponse,
    CityResponse,
    CompanyResponse,
    CompanyUpdate,
    ReportIn,
    ScoredPosting,
    SearchFilters,
    WatchIn,
)
from .monitor import loop as monitor_loop

STATIC = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    app.state.client = PoliteClient()
    task = asyncio.create_task(monitor_loop(app.state.client)) if settings.monitor_enabled else None
    yield
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    await app.state.client.aclose()


app = FastAPI(title="Ghost Job Radar", version=__version__, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC), name="static")
# only the browser extension may call the local API cross-origin; ordinary websites may not
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.cors_origin_regex,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _client(request: Request) -> PoliteClient:
    return request.app.state.client


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/api/meta")
async def meta() -> dict:
    table = baselines.load_table()
    return {
        "version": __version__,
        "adzuna_enabled": settings.adzuna_enabled,
        "connectors": {
            "adzuna": settings.adzuna_enabled,
            "linkedin": settings.linkedin_enabled,
            "jsearch": settings.jsearch_enabled,
            "bundesagentur": settings.ba_jobsuche,
            "arbeitnow": True,
            "employer_feeds": True,
        },
        "monitor_enabled": settings.monitor_enabled,
        "monitor_interval_hours": settings.monitor_interval_hours,
        "baseline_year": table.year,
        "baseline_occupations": len(table.labels),
    }


@app.post("/api/check", response_model=CheckResponse)
async def check(req: CheckRequest, request: Request) -> CheckResponse:
    return await services.check_posting(_client(request), req)


@app.get("/api/company", response_model=CompanyResponse)
async def company(
    request: Request,
    name: str = Query(..., min_length=2, max_length=120),
    careers_url: str | None = Query(None, max_length=500),
    news: bool = True,
) -> CompanyResponse:
    return await services.company_report(_client(request), name.strip(), careers_url, with_news=news)


@app.put("/api/company/{company_id}")
async def update_company(company_id: int, body: CompanyUpdate) -> dict:
    """Save what the user knows about an employer; fields sent empty are cleared, fields left out are kept."""
    if not db.get_company(company_id):
        raise HTTPException(404, "Unknown company")
    fields = body.model_dump(exclude_unset=True)
    for key, value in fields.items():
        if isinstance(value, date):
            fields[key] = value.isoformat()
        elif isinstance(value, str):
            fields[key] = value.strip() or None
        elif key in {"headcount", "headcount_prev"} and not value:
            fields[key] = None
    db.update_company(company_id, **fields)
    return {"ok": True}


@app.get("/api/city", response_model=CityResponse)
async def city(
    request: Request,
    city: str = Query(..., min_length=2, max_length=80),
    q: str | None = Query(None, max_length=80),
    radius: int = Query(20, ge=1, le=100),
    arbeitnow: bool = True,
    posted_within: int | None = Query(None, ge=1, le=90),
    job_type: Literal["full_time", "part_time", "contract", "internship"] | None = None,
    remote: bool = False,
    exclude_agencies: bool = False,
    sources: str | None = Query(None, max_length=100, description="comma list: linkedin,ba,jsearch,adzuna,arbeitnow,tracked"),
    texts: bool = Query(True, description="read missing ad texts in the background (off for refreshes)"),
) -> CityResponse:
    filters = SearchFilters(posted_within=posted_within, job_type=job_type, remote=remote, exclude_agencies=exclude_agencies)
    if sources:
        filters.sources = [s.strip() for s in sources.split(",") if s.strip()]
    return await services.city_report(_client(request), city.strip(), q, radius, arbeitnow, filters, read_texts=texts)


# ------------------------------------------------------------------ background tasks with progress


@app.post("/api/tasks/check")
async def task_check(req: CheckRequest, request: Request) -> dict:
    client = _client(request)
    return {"task_id": tasks.start("Checking the posting", lambda p: services.check_posting(client, req, p))}


@app.post("/api/tasks/company")
async def task_company(
    request: Request,
    name: str = Query(..., min_length=2, max_length=120),
    careers_url: str | None = Query(None, max_length=500),
    news: bool = True,
) -> dict:
    client = _client(request)
    return {"task_id": tasks.start(f"Analysing {name.strip()}",
                                   lambda p: services.company_report(client, name.strip(), careers_url, news, p))}


@app.post("/api/tasks/city")
async def task_city(
    request: Request,
    city: str = Query(..., min_length=2, max_length=80),
    q: str | None = Query(None, max_length=80),
    radius: int = Query(20, ge=1, le=100),
    posted_within: int | None = Query(None, ge=1, le=90),
    job_type: Literal["full_time", "part_time", "contract", "internship"] | None = None,
    remote: bool = False,
    exclude_agencies: bool = False,
    sources: str | None = Query(None, max_length=100),
) -> dict:
    client = _client(request)
    filters = SearchFilters(posted_within=posted_within, job_type=job_type, remote=remote, exclude_agencies=exclude_agencies)
    if sources:
        filters.sources = [s.strip() for s in sources.split(",") if s.strip()]
    return {"task_id": tasks.start(f"Searching {city.strip()}",
                                   lambda p: services.city_report(client, city.strip(), q, radius, True, filters, p))}


@app.get("/api/tasks/{task_id}")
async def task_status(task_id: str) -> dict:
    data = tasks.status(task_id)
    if data is None:
        raise HTTPException(404, "Unknown or expired task")
    return data


@app.get("/api/company/{company_id}/news")
async def company_news(company_id: int, request: Request) -> dict:
    data = services.news_state(_client(request), company_id)
    if data is None:
        raise HTTPException(404, "Unknown company")
    return data


@app.post("/api/capture", response_model=CheckResponse)
async def capture(body: CaptureIn, request: Request) -> CheckResponse:
    """A job page captured in the user's own browser by the extension."""
    return await services.capture_posting(_client(request), body)


@app.get("/api/overview")
async def overview() -> dict:
    """Everything stored so far, scored (cached until the database changes)."""
    return await asyncio.to_thread(services.overview)


@app.get("/api/postings/{posting_id}", response_model=ScoredPosting)
async def posting(posting_id: int) -> ScoredPosting:
    scored = services.scored_posting(posting_id)
    if scored is None:
        raise HTTPException(404, "Unknown posting")
    return scored


@app.get("/api/postings/{posting_id}/timeline")
async def posting_timeline(posting_id: int) -> dict:
    data = services.posting_timeline(posting_id)
    if data is None:
        raise HTTPException(404, "Unknown posting")
    return data


@app.get("/api/postings/{posting_id}/history")
async def posting_history(posting_id: int) -> dict:
    data = services.posting_history(posting_id)
    if not data:
        raise HTTPException(404, "Unknown posting")
    return data


@app.post("/api/reports")
async def add_report(body: ReportIn) -> dict:
    if not (body.posting_id or body.posting_url or body.company):
        raise HTTPException(422, "Give a posting or a company.")
    data = body.model_dump()
    if body.posting_id and not body.company:
        row = db.get_posting_row(body.posting_id, light=True)
        data["company"] = row.get("company") if row else None
    if body.posting_id:
        data["risk"], data["snapshot"] = await asyncio.to_thread(services.snapshot, body.posting_id)
    return {"id": db.add_report(data)}


@app.get("/api/model")
async def model_status() -> dict:
    """Ground truth, labelling functions, survival baselines, the trained model and the prevalence estimate."""
    return await asyncio.to_thread(services.model_status)


@app.post("/api/model/train")
async def model_train() -> dict:
    return await asyncio.to_thread(ml_model.train)


@app.get("/api/audit/queue")
async def audit_queue(n: int = Query(12, ge=4, le=40), redraw: bool = False) -> dict:
    return await asyncio.to_thread(services.audit_queue, n, redraw)


@app.post("/api/audit")
async def add_audit(body: AuditIn) -> dict:
    if not db.get_posting_row(body.posting_id, light=True):
        raise HTTPException(404, "Unknown posting")
    audit_id = await asyncio.to_thread(services.record_audit, body.posting_id, body.label, body.method, body.note,
                                       body.inclusion_prob, body.approval, body.manager_named, body.start_date_given)
    return {"id": audit_id}


@app.get("/api/prefs")
async def get_prefs() -> dict:
    return {**user_prefs.get(), "windows": list(user_prefs.WINDOWS)}


@app.put("/api/prefs")
async def put_prefs(body: PrefsIn) -> dict:
    values = body.model_dump(exclude_unset=True)
    if "chance_high" in values and "chance_very_high" in values and values["chance_very_high"] <= values["chance_high"]:
        raise HTTPException(422, "The 'very low chance' threshold must be above the 'low chance' threshold.")
    return {**user_prefs.save(values), "windows": list(user_prefs.WINDOWS)}


@app.post("/api/company/{company_id}/events")
async def add_company_event(company_id: int, body: EventIn) -> dict:
    if not db.get_company(company_id):
        raise HTTPException(404, "Unknown company")
    services.add_employer_event(company_id, body.kind, body.date, body.note)
    return {"ok": True}


@app.delete("/api/company/{company_id}/events/{event_id}")
async def delete_company_event(company_id: int, event_id: int) -> dict:
    if not db.delete_note_event(company_id, event_id):
        raise HTTPException(404, "Only your own notes can be removed.")
    return {"ok": True}


@app.get("/api/notes")
async def noted_companies() -> list[dict]:
    return db.noted_companies()


@app.post("/api/notes/import")
async def import_notes(body: NotesImport) -> dict:
    return services.import_notes(body.csv)


@app.get("/api/postings/{posting_id}/evidence")
async def posting_evidence(posting_id: int) -> list[dict]:
    if not db.get_posting_row(posting_id, light=True):
        raise HTTPException(404, "Unknown posting")
    return await asyncio.to_thread(services.evidence_log, posting_id)


@app.get("/api/reports")
async def list_reports(company: str | None = None, posting_id: int | None = None) -> list[dict]:
    return db.report_rows(company=company, posting_id=posting_id)


@app.get("/api/watchlist")
async def watchlist() -> list[dict]:
    return db.watch_list()


@app.post("/api/watchlist")
async def add_watch(body: WatchIn) -> dict:
    return {"id": db.watch_add(body.kind, body.query, body.params)}


@app.delete("/api/watchlist/{item_id}")
async def delete_watch(item_id: int) -> dict:
    db.watch_delete(item_id)
    return {"ok": True}


@app.post("/api/watchlist/{item_id}/run")
async def run_watch(item_id: int, request: Request) -> dict:
    item = db.watch_get(item_id)
    if not item:
        raise HTTPException(404, "Unknown watch item")
    return await services.run_watch_item(_client(request), item)
