"""SERVE API (FastAPI).

Member routes act as the single demo member (no member login in this prototype).
Admin routes require the X-Admin-Token header — a shared demo token, not real
user authentication. Only POST /api/admin/requests/{id}/approve creates bookings.
"""

from __future__ import annotations

import json
import re
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, field_validator

from . import config, defenses as dfn, scheduling as sch
from .db import connect, init_db, today
from .pipeline import (WorkflowError, default_profile, append_member_reply, approve_request, cancel_booking, create_ai_request,
                       create_slot_request, decide_request, process_request)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    print(f"SERVE backend ready. Model: {config.MODEL_NAME}. "
          f"Credentials: {'Portkey' if config.portkey_key() else 'OpenAI' if config.openai_key() else 'NONE FOUND'}.")
    if config.ADMIN_TOKEN_GENERATED:
        print(f"Admin token for this run (set SERVE_ADMIN_TOKEN in .env to fix it): {config.ADMIN_TOKEN}")
    yield


app = FastAPI(title="SERVE API", lifespan=lifespan)


@app.exception_handler(WorkflowError)
async def workflow_error(_req: Request, exc: WorkflowError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message, "problems": exc.details})


def db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


_ADMIN_FAILS: dict[str, deque] = defaultdict(deque)


def require_admin(request: Request, x_admin_token: str = Header(default="")) -> None:
    """Shared-token check on every admin route. D6: after repeated bad tokens from one
    client, further attempts are refused for a few minutes."""
    client = request.client.host if request.client else "unknown"
    fails = _ADMIN_FAILS[client]
    now = time.monotonic()
    while fails and now - fails[0] > dfn.ADMIN_LOCK_SECONDS:
        fails.popleft()
    if dfn.enabled() and len(fails) >= dfn.ADMIN_FAILS_BEFORE_LOCK:
        raise HTTPException(status_code=429, detail="Too many failed admin sign-in attempts. Try again later.")
    if not secrets.compare_digest(x_admin_token.encode(), config.ADMIN_TOKEN.encode()):
        fails.append(now)
        raise HTTPException(status_code=401, detail="Admin token required.")


_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(v: str) -> str:
    return _CONTROL.sub("", v).strip()


# ---------------------------------------------------------------------------
# request bodies
# ---------------------------------------------------------------------------

class AIRequestIn(BaseModel):
    text: str = Field(min_length=10, max_length=1500)

    @field_validator("text")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = clean_text(v)
        if len(v) < 2:
            raise ValueError("Text is empty after removing control characters.")
        return v


class FormRequestIn(BaseModel):
    service_id: str = Field(max_length=40)
    preferred_date: str = Field(min_length=3, max_length=60)
    alternate_date: str | None = Field(default=None, max_length=60)
    notes: str | None = Field(default=None, max_length=800)


class SlotRequestIn(BaseModel):
    service_id: str = Field(max_length=40)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")


class ReplyIn(BaseModel):
    text: str = Field(min_length=2, max_length=800)

    @field_validator("text")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = clean_text(v)
        if len(v) < 2:
            raise ValueError("Text is empty after removing control characters.")
        return v


class SlotIn(BaseModel):
    service_id: str | None = Field(default=None, max_length=40)
    priest_id: str = Field(max_length=40)
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$")
    location_type: Literal["temple", "home"]
    city: str | None = Field(default=None, max_length=60)
    language: str | None = Field(default=None, max_length=30)


class ApproveIn(BaseModel):
    admin_name: str = Field(min_length=2, max_length=60)
    option_index: int | None = Field(default=None, ge=0, le=5)
    slot: SlotIn | None = None
    note: str | None = Field(default=None, max_length=500)


class DecisionIn(BaseModel):
    admin_name: str = Field(min_length=2, max_length=60)
    message: str = Field(min_length=3, max_length=600)


class CancelIn(BaseModel):
    admin_name: str = Field(min_length=2, max_length=60)
    reason: str = Field(min_length=3, max_length=300)


# ---------------------------------------------------------------------------
# serializers
# ---------------------------------------------------------------------------

def _j(v, default=None):
    return json.loads(v) if v else default


def booking_out(conn, b) -> dict:
    svc = conn.execute("SELECT name FROM services WHERE id = ?", (b["service_id"],)).fetchone()
    pr = conn.execute("SELECT name FROM priests WHERE id = ?", (b["priest_id"],)).fetchone()
    m = conn.execute("SELECT name FROM members WHERE id = ?", (b["member_id"],)).fetchone()
    z = conn.execute("SELECT display_name FROM travel_zones WHERE city = ?", (b["city"],)).fetchone() if b["city"] else None
    return {**dict(b), "service_name": svc["name"], "priest_name": pr["name"], "member_name": m["name"],
            "city_display": z["display_name"] if z else b["city"]}


def member_request_out(conn, r) -> dict:
    rec = _j(r["recommendation_json"], {})
    intake = _j(r["intake_json"], {})
    svc = conn.execute("SELECT name FROM services WHERE id = ?", (intake.get("service_id"),)).fetchone() if intake.get("service_id") else None
    booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (r["booking_id"],)).fetchone() if r["booking_id"] else None
    options = [{k: o.get(k) for k in ("priest_name", "date", "start_time", "end_time", "location_type", "city",
                                       "total_cents", "travel_fee_cents")} for o in rec.get("options", [])]
    return {
        "id": r["id"], "source": r["source"], "status": r["status"], "raw_text": r["raw_text"],
        "service_name": svc["name"] if svc else None, "member_message": r["member_message"],
        "proposed_options": options if r["status"] == "pending_review" else [],
        "booking": booking_out(conn, booking) if booking else None,
        "created_at": r["created_at"], "updated_at": r["updated_at"],
    }


def services_out(conn) -> list[dict]:
    out = []
    for s in conn.execute("SELECT * FROM services ORDER BY rowid"):
        out.append({
            "id": s["id"], "organizationId": "org_shanti_mandir", "name": s["name"], "category": s["category"],
            "priceCents": s["price_cents"], "priceLabel": s["price_label"], "durationMinutes": s["duration_minutes"],
            "durationLabel": s["duration_label"], "summary": s["summary"], "description": s["description"],
            "location": s["location_label"], "thingsToKnow": _j(s["things_to_know"], []),
            "scheduling": s["scheduling"], "locationMode": s["location_mode"],
            "slots": sch.fixed_slot_calendar(conn, s["id"]) if s["scheduling"] == "fixed_slots" else None,
            "enabled": bool(s["enabled"]), "popular": bool(s["popular"]),
        })
    return out


def events_out(conn) -> list[dict]:
    return [{
        "id": e["id"], "organizationId": "org_shanti_mandir", "name": e["name"], "isoDate": e["date"],
        "startTime": e["start_time"], "endTime": e["end_time"], "location": e["location"], "summary": e["summary"],
        "description": e["description"], "image": e["image"],
        "volunteerOpportunityIds": _j(e["volunteer_opportunity_ids"], []),
    } for e in conn.execute("SELECT * FROM events WHERE date >= ? ORDER BY date, start_time", (today().isoformat(),))]


# ---------------------------------------------------------------------------
# member routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"ok": True, "model": config.MODEL_NAME, "agent_profile": default_profile(),
            "defenses": "on" if dfn.enabled() else "off",
            "credentials": "portkey" if config.portkey_key() else "openai" if config.openai_key() else None,
            "env_files_loaded": len(config.LOADED_ENV_FILES), "today": today().isoformat()}


@app.get("/api/portal")
def portal(conn=Depends(db)):
    mid = config.DEMO_MEMBER_ID
    m = conn.execute("SELECT * FROM members WHERE id = ?", (mid,)).fetchone()
    reqs = conn.execute("SELECT * FROM service_requests WHERE member_id = ? ORDER BY created_at DESC", (mid,)).fetchall()
    bks = conn.execute("SELECT * FROM bookings WHERE member_id = ? ORDER BY date, start_time", (mid,)).fetchall()
    return {
        "today": today().isoformat(),
        "demo_notice": conn.execute("SELECT value FROM meta WHERE key = 'demo_notice'").fetchone()[0],
        "member": {"id": m["id"], "name": m["name"], "email": m["email"]},
        "events": events_out(conn), "services": services_out(conn),
        "requests": [member_request_out(conn, r) for r in reqs],
        "bookings": [booking_out(conn, b) for b in bks],
    }


@app.post("/api/requests", status_code=202)
def submit_ai_request(body: AIRequestIn, bg: BackgroundTasks, conn=Depends(db)):
    rid, reused = create_ai_request(conn, member_id=config.DEMO_MEMBER_ID, text=body.text, source="ai_request",
                                    return_reused=True)
    if not reused:
        bg.add_task(process_request, rid)
    return member_request_out(conn, conn.execute("SELECT * FROM service_requests WHERE id = ?", (rid,)).fetchone())


@app.post("/api/requests/form", status_code=202)
def submit_form_request(body: FormRequestIn, bg: BackgroundTasks, conn=Depends(db)):
    svc = conn.execute("SELECT name, scheduling FROM services WHERE id = ? AND enabled = 1", (body.service_id,)).fetchone()
    if not svc:
        raise HTTPException(404, "Unknown service.")
    parts = [f"I would like to request {svc['name']}.", f"Preferred date: {clean_text(body.preferred_date)}."]
    if body.alternate_date:
        parts.append(f"Alternate date: {clean_text(body.alternate_date)}.")
    if body.notes:
        parts.append(f"Notes: {clean_text(body.notes)}")
    rid, reused = create_ai_request(conn, member_id=config.DEMO_MEMBER_ID, text=" ".join(parts), source="request_form",
                                    return_reused=True)
    if not reused:
        bg.add_task(process_request, rid)
    return member_request_out(conn, conn.execute("SELECT * FROM service_requests WHERE id = ?", (rid,)).fetchone())


@app.post("/api/requests/slot", status_code=201)
def submit_slot_request(body: SlotRequestIn, conn=Depends(db)):
    rid = create_slot_request(conn, member_id=config.DEMO_MEMBER_ID, service_id=body.service_id,
                              date_str=body.date, start_time=body.start_time)
    return member_request_out(conn, conn.execute("SELECT * FROM service_requests WHERE id = ?", (rid,)).fetchone())


@app.get("/api/requests/{request_id}")
def get_my_request(request_id: str, conn=Depends(db)):
    r = conn.execute("SELECT * FROM service_requests WHERE id = ? AND member_id = ?",
                     (request_id, config.DEMO_MEMBER_ID)).fetchone()
    if not r:
        raise HTTPException(404, "Request not found.")
    return member_request_out(conn, r)


@app.post("/api/requests/{request_id}/reply", status_code=202)
def reply_to_request(request_id: str, body: ReplyIn, bg: BackgroundTasks, conn=Depends(db)):
    append_member_reply(conn, request_id=request_id, member_id=config.DEMO_MEMBER_ID, text=body.text)
    bg.add_task(process_request, request_id)
    return member_request_out(conn, conn.execute("SELECT * FROM service_requests WHERE id = ?", (request_id,)).fetchone())


# ---------------------------------------------------------------------------
# admin routes
# ---------------------------------------------------------------------------

admin = [Depends(require_admin)]


def _runs_for(conn, request_id: str) -> list[dict]:
    runs = []
    for r in conn.execute("SELECT * FROM agent_runs WHERE request_id = ? ORDER BY started_at", (request_id,)):
        d = dict(r)
        d["cost_breakdown"] = _j(d["cost_breakdown"])
        d["output"] = _j(d.pop("output_json"))
        d["tool_call_log"] = [{**dict(t), "args": _j(t["args_json"])} for t in conn.execute(
            "SELECT tool_name, args_json, result_summary, ok, duration_ms, called_at FROM tool_calls WHERE run_id = ? ORDER BY id",
            (r["id"],))]
        runs.append(d)
    return runs


@app.get("/api/admin/session", dependencies=admin)
def admin_session():
    return {"ok": True}


@app.get("/api/admin/summary", dependencies=admin)
def admin_summary(conn=Depends(db)):
    counts = {r[0]: r[1] for r in conn.execute("SELECT status, COUNT(*) FROM service_requests GROUP BY status")}
    upcoming = conn.execute("SELECT COUNT(*) FROM bookings WHERE status = 'confirmed' AND date >= ?",
                            (today().isoformat(),)).fetchone()[0]
    ai = conn.execute("SELECT COUNT(*), COALESCE(SUM(cost_usd),0), COALESCE(SUM(input_tokens),0), "
                      "COALESCE(SUM(output_tokens),0) FROM agent_runs").fetchone()
    return {"requests_by_status": counts, "upcoming_bookings": upcoming,
            "agent_runs": ai[0], "ai_cost_usd": ai[1], "input_tokens": ai[2], "output_tokens": ai[3]}


@app.get("/api/admin/requests", dependencies=admin)
def admin_requests(status: str | None = None, conn=Depends(db)):
    q = ("SELECT r.*, m.name AS member_name FROM service_requests r JOIN members m ON m.id = r.member_id"
         + (" WHERE r.status = ?" if status else "") + " ORDER BY r.created_at DESC LIMIT 200")
    rows = conn.execute(q, (status,) if status else ()).fetchall()
    out = []
    for r in rows:
        intake = _j(r["intake_json"], {})
        rec = _j(r["recommendation_json"], {})
        svc = conn.execute("SELECT name FROM services WHERE id = ?", (intake.get("service_id"),)).fetchone() if intake.get("service_id") else None
        out.append({"id": r["id"], "member_name": r["member_name"], "status": r["status"], "source": r["source"],
                    "service_name": svc["name"] if svc else None, "summary": intake.get("summary") or r["raw_text"][:120],
                    "option_count": len(rec.get("options", [])), "created_at": r["created_at"],
                    "risk_flags": _j(r["risk_flags"], {})})
    return out


@app.get("/api/admin/requests/{request_id}", dependencies=admin)
def admin_request_detail(request_id: str, conn=Depends(db)):
    r = conn.execute("SELECT r.*, m.name AS member_name, m.email AS member_email FROM service_requests r "
                     "JOIN members m ON m.id = r.member_id WHERE r.id = ?", (request_id,)).fetchone()
    if not r:
        raise HTTPException(404, "Request not found.")
    booking = conn.execute("SELECT * FROM bookings WHERE id = ?", (r["booking_id"],)).fetchone() if r["booking_id"] else None
    return {
        "request": {k: r[k] for k in r.keys() if k not in ("intake_json", "recommendation_json", "missing_info", "risk_flags")},
        "intake": _j(r["intake_json"]), "recommendation": _j(r["recommendation_json"]),
        "service_name": (lambda i: (conn.execute("SELECT name FROM services WHERE id = ?", (i,)).fetchone() or [None])[0]
                         if i else None)((_j(r["intake_json"], {}) or {}).get("service_id")),
        "missing_info": _j(r["missing_info"], []),
        "risk_flags": _j(r["risk_flags"], {}),
        "agent_runs": _runs_for(conn, request_id),
        "approvals": [dict(a) for a in conn.execute("SELECT * FROM approvals WHERE request_id = ? ORDER BY id", (request_id,))],
        "audit": [dict(a) for a in conn.execute("SELECT * FROM audit_events WHERE request_id = ? ORDER BY id", (request_id,))],
        "booking": booking_out(conn, booking) if booking else None,
    }


def _slot_from(conn, request_id: str, body: ApproveIn) -> tuple[dict, bool]:
    r = conn.execute("SELECT intake_json, recommendation_json FROM service_requests WHERE id = ?", (request_id,)).fetchone()
    if not r:
        raise HTTPException(404, "Request not found.")
    if body.slot is not None:
        slot = body.slot.model_dump()
        slot["service_id"] = slot["service_id"] or _j(r["intake_json"], {}).get("service_id")
        if not slot["service_id"]:
            raise HTTPException(422, "service_id is required when the request has no identified service.")
        return slot, True
    if body.option_index is None:
        raise HTTPException(422, "Provide option_index or slot.")
    options = _j(r["recommendation_json"], {}).get("options", [])
    if body.option_index >= len(options):
        raise HTTPException(422, "No such recommended option.")
    o = options[body.option_index]
    return {k: o.get(k) for k in ("service_id", "priest_id", "date", "start_time", "location_type", "city", "language")}, False


@app.post("/api/admin/requests/{request_id}/approve", dependencies=admin)
def admin_approve(request_id: str, body: ApproveIn, conn=Depends(db)):
    slot, edited = _slot_from(conn, request_id, body)
    result = approve_request(conn, request_id=request_id, slot=slot, admin_name=clean_text(body.admin_name),
                             note=clean_text(body.note) if body.note else None, edited=edited)
    return {"ok": True, **result}


@app.post("/api/admin/requests/{request_id}/reject", dependencies=admin)
def admin_reject(request_id: str, body: DecisionIn, conn=Depends(db)):
    decide_request(conn, request_id=request_id, decision="rejected", admin_name=clean_text(body.admin_name),
                   message=clean_text(body.message))
    return {"ok": True}


@app.post("/api/admin/requests/{request_id}/needs-info", dependencies=admin)
def admin_needs_info(request_id: str, body: DecisionIn, conn=Depends(db)):
    decide_request(conn, request_id=request_id, decision="needs_info", admin_name=clean_text(body.admin_name),
                   message=clean_text(body.message))
    return {"ok": True}


@app.post("/api/admin/check-slot", dependencies=admin)
def admin_check_slot(body: SlotIn, conn=Depends(db)):
    if not body.service_id:
        raise HTTPException(422, "service_id is required.")
    return sch.check_slot(conn, service_id=body.service_id, priest_id=body.priest_id, date_str=body.date,
                          start_time=body.start_time, location_type=body.location_type, city=body.city,
                          language=body.language)


@app.get("/api/admin/reference", dependencies=admin)
def admin_reference(conn=Depends(db)):
    return {
        "priests": [{**dict(p), "languages": sch._languages(conn, p["id"]),
                     "qualifications": [q[0] for q in conn.execute("SELECT service_id FROM priest_qualifications WHERE priest_id = ?", (p["id"],))]}
                    for p in conn.execute("SELECT * FROM priests ORDER BY name")],
        "services": [{"id": s["id"], "name": s["name"], "location_mode": s["location_mode"],
                      "slot_times": _j(s["slot_times"])} for s in conn.execute("SELECT * FROM services ORDER BY name")],
        "towns": [z["display_name"] for z in conn.execute("SELECT display_name FROM travel_zones ORDER BY display_name")],
    }


@app.get("/api/admin/bookings", dependencies=admin)
def admin_bookings(conn=Depends(db)):
    rows = conn.execute("SELECT * FROM bookings ORDER BY date, start_time").fetchall()
    return [booking_out(conn, b) for b in rows]


@app.post("/api/admin/bookings/{booking_id}/cancel", dependencies=admin)
def admin_cancel(booking_id: str, body: CancelIn, conn=Depends(db)):
    cancel_booking(conn, booking_id=booking_id, admin_name=clean_text(body.admin_name), reason=clean_text(body.reason))
    return {"ok": True}


@app.get("/api/admin/agent-runs", dependencies=admin)
def admin_agent_runs(conn=Depends(db)):
    runs = [dict(r) for r in conn.execute(
        "SELECT a.id, a.request_id, a.agent, a.model, a.response_model, a.started_at, a.latency_ms, a.status, a.error, "
        "a.model_requests, a.input_tokens, a.cached_input_tokens, a.cache_write_tokens, a.output_tokens, "
        "a.reasoning_tokens, a.tool_calls, a.cost_usd FROM agent_runs a ORDER BY a.started_at DESC")]
    totals = {k: sum((r[k] or 0) for r in runs) for k in
              ("input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens", "reasoning_tokens",
               "tool_calls", "model_requests", "cost_usd")}
    totals["runs"] = len(runs)
    return {"runs": runs, "totals": totals, "pricing": json.loads(config.PRICES_PATH.read_text())}


@app.get("/api/admin/audit", dependencies=admin)
def admin_audit(limit: int = 200, conn=Depends(db)):
    limit = max(1, min(limit, 1000))
    return [dict(a) for a in conn.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT ?", (limit,))]


# ---------------------------------------------------------------------------
# built frontend (single-port mode after `npm run build`)
# ---------------------------------------------------------------------------

if config.FRONTEND_DIST.is_dir():
    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith("api/"):
            raise HTTPException(404)
        target = (config.FRONTEND_DIST / path).resolve()
        if path and target.is_file() and config.FRONTEND_DIST.resolve() in target.parents:
            return FileResponse(target)
        return FileResponse(config.FRONTEND_DIST / "index.html")
