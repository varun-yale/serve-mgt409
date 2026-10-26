"""Request workflow: Intake Agent -> deterministic checks -> Scheduling Agent ->
rules-engine re-verification -> admin review queue. Plus the approval logic.

Every agent run is stored in `agent_runs` with the token counts the API
returned and the cost computed from prices.json; every tool call goes to
`tool_calls`; every state change goes to `audit_events`.
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from pydantic_ai import capture_run_messages
from pydantic_ai.messages import ModelResponse

from . import config, defenses as dfn, scheduling as sch
from .agents import (HTTP_LOG, INTAKE_LIMITS, RUN_TIMEOUT_SECONDS, SCHEDULING_LIMITS, Deps, IntakeResult,
                     ScheduleRecommendation, build_intake_agent, build_model, build_scheduling_agent,
                     deterministic_missing, intake_user_prompt, scheduling_user_prompt)
from .db import audit, connect, now_iso

PIPELINE_SLOTS = asyncio.Semaphore(2)  # at most two requests processed by agents at once
OPEN_STATUSES = ("processing", "pending_review", "needs_info")
MAX_OPEN_REQUESTS_PER_MEMBER = 6


def default_profile() -> str:
    return os.getenv("SERVE_AGENT_PROFILE", "optimized")


class WorkflowError(Exception):
    def __init__(self, status_code: int, message: str, details: Any = None):
        super().__init__(message)
        self.status_code, self.message, self.details = status_code, message, details


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


# ---------------------------------------------------------------------------
# cost
# ---------------------------------------------------------------------------

def cost_usd(input_tokens: int, cached: int, cache_write: int, output_tokens: int) -> dict:
    """Dollar cost from the API's own token counts. input_tokens includes cached
    tokens, so cached reads are billed at the cached rate and only the rest at the
    full input rate."""
    p = json.loads(config.PRICES_PATH.read_text())[config.MODEL_NAME]
    per = lambda k: Decimal(str(p[k])) / Decimal(1_000_000)  # noqa: E731
    uncached = max(0, input_tokens - cached - cache_write)
    parts = {
        "uncached_input": uncached * per("input_per_1m"),
        "cached_input": cached * per("cached_input_per_1m"),
        "cache_write": cache_write * per("cache_write_per_1m"),
        "output": output_tokens * per("output_per_1m"),
    }
    return {k: float(v) for k, v in parts.items()} | {"total": float(sum(parts.values()))}


# ---------------------------------------------------------------------------
# running one agent with full logging
# ---------------------------------------------------------------------------

async def run_agent(conn: sqlite3.Connection, *, agent, agent_name: str, prompt: str, request_id: str,
                    member_id: str, limits, profile: str = "standard", tool_budgets: bool = True) -> tuple[Any | None, dict]:
    run_id = new_id("run")
    started = now_iso()
    conn.execute("INSERT INTO agent_runs (id, request_id, agent, model, started_at, status) VALUES (?,?,?,?,?, 'running')",
                 (run_id, request_id, agent_name, config.MODEL_NAME, started))
    deps = Deps(conn=conn, member_id=member_id, agent=agent_name, profile=profile, tool_budgets=tool_budgets)
    t0 = time.perf_counter()
    output, error = None, None
    http_log: list[dict] = []
    token = HTTP_LOG.set(http_log)
    with capture_run_messages() as messages:
        try:
            result = await asyncio.wait_for(agent.run(prompt, deps=deps, usage_limits=limits),
                                            timeout=RUN_TIMEOUT_SECONDS)
            output = result.output
        except Exception as exc:  # recorded and surfaced; no fallback model
            error = f"{type(exc).__name__}: {str(exc)[:600]}"
        finally:
            HTTP_LOG.reset(token)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    # Token counts come from each model response the API returned.
    responses = [m for m in messages if isinstance(m, ModelResponse)]
    tot = {"input": 0, "cached": 0, "cache_write": 0, "output": 0, "reasoning": 0}
    for r in responses:
        u = r.usage
        tot["input"] += u.input_tokens or 0
        tot["cached"] += u.cache_read_tokens or 0
        tot["cache_write"] += u.cache_write_tokens or 0
        tot["output"] += u.output_tokens or 0
        tot["reasoning"] += (u.output_reasoning_tokens or (u.details or {}).get("reasoning_tokens") or 0)
    cost = cost_usd(tot["input"], tot["cached"], tot["cache_write"], tot["output"])
    response_model = responses[-1].model_name if responses else None
    # Model guard: Portkey routes through a multi-target config, so refuse any
    # response that did not come from a gpt-6-luna deployment.
    wrong = sorted({r.model_name for r in responses if r.model_name and not r.model_name.startswith(config.MODEL_NAME)})
    if wrong and error is None:
        error, output = f"ModelMismatch: requested {config.MODEL_NAME}, API reported {', '.join(wrong)}", None
    cache_hits = sum(1 for h in http_log if (h.get("portkey_cache_status") or "").upper() == "HIT")

    conn.execute(
        """UPDATE agent_runs SET response_model=?, finished_at=?, latency_ms=?, status=?, error=?, model_requests=?,
           input_tokens=?, cached_input_tokens=?, cache_write_tokens=?, output_tokens=?, reasoning_tokens=?,
           tool_calls=?, cost_usd=?, cost_breakdown=?, output_json=?, provider=?, portkey_target=?,
           portkey_cache=?, portkey_cache_hits=?, http_log=? WHERE id=?""",
        (response_model, now_iso(), latency_ms, "ok" if error is None else "error", error, len(responses),
         tot["input"], tot["cached"], tot["cache_write"], tot["output"], tot["reasoning"], len(deps.trace),
         cost["total"], json.dumps(cost), output.model_dump_json() if output is not None else None,
         ",".join(sorted({h["provider"] for h in http_log if h.get("provider")})) or None,
         ",".join(sorted({h["portkey_target"] for h in http_log if h.get("portkey_target")})) or None,
         ",".join(h.get("portkey_cache_status") or "-" for h in http_log) or None, cache_hits,
         json.dumps(http_log), run_id))
    for t in deps.trace:
        conn.execute(
            """INSERT INTO tool_calls (run_id, request_id, agent, tool_name, args_json, result_summary, ok, duration_ms, called_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (run_id, request_id, agent_name, t["tool_name"], json.dumps(t["args"]), t["result_summary"],
             int(t["ok"]), t["duration_ms"], t["called_at"]))
    audit(conn, f"agent:{agent_name}", "agent_run_finished" if error is None else "agent_run_failed",
          request_id=request_id, details={"run_id": run_id, "profile": profile, "tool_calls": len(deps.trace),
                                          "cost_usd": cost["total"], "error": error,
                                          "tool_budget_refusals": sum(1 for t in deps.trace if "Tool budget" in t["result_summary"])})
    return output, {"run_id": run_id, "error": error}


# ---------------------------------------------------------------------------
# request lifecycle
# ---------------------------------------------------------------------------

def _set(conn, request_id: str, **fields) -> None:
    fields["updated_at"] = now_iso()
    cols = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE service_requests SET {cols} WHERE id = ?", (*fields.values(), request_id))


def check_open_request_limit(conn, member_id: str) -> None:
    n = conn.execute(f"SELECT COUNT(*) FROM service_requests WHERE member_id = ? AND status IN ({','.join('?' * len(OPEN_STATUSES))})",
                     (member_id, *OPEN_STATUSES)).fetchone()[0]
    if n >= MAX_OPEN_REQUESTS_PER_MEMBER:
        raise WorkflowError(429, f"You already have {n} open requests. Please wait for the office to review them.")


def create_ai_request(conn, *, member_id: str, text: str, source: str, defenses: bool | None = None,
                      return_reused: bool = False):
    """Store a new request. With defenses on: D1 sanitize, D2 screen, D4 dedupe + rate cap.
    Returns the request id (an existing one if this is a duplicate of an open request)."""
    on = dfn.enabled() if defenses is None else defenses
    flags: dict = {}
    if on:
        raw = text
        text, changes = dfn.sanitize(text)
        # Screen both the raw text (sees delimiter tags before D1 neutralizes them) and the cleaned text.
        hits = sorted(set(dfn.screen(raw)) | set(dfn.screen(text)))
        if changes:
            flags["sanitized"] = changes
        if hits:
            flags["injection_patterns"] = hits
        recent = conn.execute(
            "SELECT id, raw_text, status FROM service_requests WHERE member_id = ? AND created_at >= ? ORDER BY created_at DESC",
            (member_id, (datetime.now(config.TIMEZONE) - timedelta(minutes=10)).isoformat(timespec="seconds"))).fetchall()
        key = dfn.normalize_for_dedupe(text)
        for r in recent:
            if r["status"] in OPEN_STATUSES and dfn.normalize_for_dedupe(r["raw_text"]) == key:
                audit(conn, f"member:{member_id}", "duplicate_request_reused", request_id=r["id"], details={"layer": "D4"})
                return (r["id"], True) if return_reused else r["id"]
        if len(recent) >= dfn.MAX_SUBMISSIONS_PER_10_MIN:
            audit(conn, f"member:{member_id}", "rate_limited", details={"layer": "D4", "recent": len(recent)})
            raise WorkflowError(429, "Too many requests in a short time. Please wait a few minutes.")
    check_open_request_limit(conn, member_id)
    rid = new_id("req")
    ts = now_iso()
    conn.execute("INSERT INTO service_requests (id, member_id, source, raw_text, status, risk_flags, created_at, updated_at) "
                 "VALUES (?,?,?,?, 'processing', ?, ?, ?)",
                 (rid, member_id, source, text, json.dumps(flags) if flags else None, ts, ts))
    audit(conn, f"member:{member_id}", "request_submitted", request_id=rid, details={"source": source, "chars": len(text)})
    if flags.get("injection_patterns"):
        audit(conn, "system", "injection_suspected", request_id=rid, details={"layer": "D2", **flags})
    return (rid, False) if return_reused else rid


def _options_message(n: int) -> str:
    return (f"Thank you. We found {n} possible time{'s' if n != 1 else ''} that fit your request. "
            "The temple office will review and confirm one with you. Nothing is booked until the office approves it.")


async def process_request(request_id: str, profile: str | None = None, defenses: bool | None = None) -> None:
    """Run both agents for one request. Never raises: failures are stored on the request."""
    async with PIPELINE_SLOTS:
        conn = connect()
        try:
            await _process(conn, request_id, profile or default_profile(),
                           dfn.enabled() if defenses is None else defenses)
        except Exception as exc:
            _set(conn, request_id, status="failed", error=f"{type(exc).__name__}: {str(exc)[:500]}",
                 member_message="We couldn't process this request automatically. The temple office has it and will follow up.")
            audit(conn, "system", "request_failed", request_id=request_id, details={"error": str(exc)[:500]})
        finally:
            conn.close()


async def _process(conn, request_id: str, profile: str, defended: bool) -> None:
    req = conn.execute("SELECT * FROM service_requests WHERE id = ?", (request_id,)).fetchone()
    model = build_model()
    common = {"request_id": request_id, "member_id": req["member_id"], "profile": profile, "tool_budgets": defended}

    # 1. Intake Agent
    intake_agent = build_intake_agent(model, profile, catalog=sch.service_catalog_text(conn))
    intake, info = await run_agent(conn, agent=intake_agent, agent_name="intake",
                                   prompt=intake_user_prompt(req["raw_text"]), limits=INTAKE_LIMITS, **common)
    if intake is None:
        _set(conn, request_id, status="failed", error=info["error"],
             member_message="We couldn't process this request automatically. The temple office has it and will follow up.")
        return
    assert isinstance(intake, IntakeResult)

    # Deterministic clean-up of the extraction.
    svc = sch.get_service_details(conn, intake.service_id) if intake.service_id else None
    if svc and "error" in svc:
        intake.service_id, svc = None, None
    if svc and svc["location_mode"] != "either":
        intake.location_type = svc["location_mode"]
    if intake.location_type == "temple":
        intake.city, intake.city_source = None, None
    # Time preference -> window, decided in code. Invalid exact/range times fall back to "any".
    window = sch.time_window(intake.time_preference, intake.earliest_start, intake.latest_start)
    if intake.time_preference in ("exact", "range") and window is None:
        intake.time_preference = "any"
    if window is None:
        intake.earliest_start = intake.latest_start = None
    else:
        intake.earliest_start, intake.latest_start = window
    missing = deterministic_missing(intake, conn)
    _set(conn, request_id, intake_json=intake.model_dump_json(), missing_info=json.dumps(missing))

    if not intake.is_service_request:
        _set(conn, request_id, status="needs_info", missing_info=json.dumps(["service"]),
             member_message="SERVE can help you request a temple service such as a puja, archana or housewarming. "
                            "Could you tell us which service you need and when?")
        audit(conn, "system", "status_needs_info", request_id=request_id, details={"reason": "not a service request"})
        return
    if missing:
        question = (intake.clarifying_question or "").strip()[:400]
        if defended:  # D3: member-facing model text is filtered
            question, reasons = dfn.filter_member_text(question)
            if reasons:
                _flag(conn, request_id, "output_filtered", reasons)
        question = question or ("Could you tell us the " + ", ".join(missing) + " for this request?")
        _set(conn, request_id, status="needs_info", member_message=question)
        audit(conn, "system", "status_needs_info", request_id=request_id, details={"missing": missing})
        return

    # 2. Scheduling Agent, handed the structured request
    structured = {
        "service_id": intake.service_id, "preferred_dates": intake.preferred_dates, "date_notes": intake.date_notes,
        "time_preference": intake.time_preference, "earliest_start": intake.earliest_start,
        "latest_start": intake.latest_start, "location_type": intake.location_type, "city": intake.city,
        "language": intake.language, "attendees": intake.attendees,
        "special_requirements": intake.special_requirements,
    }
    rec, info = await run_agent(
        conn, agent=build_scheduling_agent(model, profile), agent_name="scheduling",
        prompt=scheduling_user_prompt(structured), limits=SCHEDULING_LIMITS, **common)
    if rec is None:
        _set(conn, request_id, status="failed", error=info["error"],
             member_message="We couldn't check availability automatically. The temple office has your request and will follow up.")
        return
    assert isinstance(rec, ScheduleRecommendation)

    # 3. Re-verify every option with the rules engine; the model cannot override it.
    verified, dropped, seen = [], [], set()
    for opt in rec.options:
        key = (opt.priest_id, opt.date, opt.start_time)
        if key in seen:
            continue
        seen.add(key)
        check = sch.check_slot(conn, service_id=intake.service_id, priest_id=opt.priest_id, date_str=opt.date,
                               start_time=opt.start_time, location_type=intake.location_type,
                               city=intake.city, language=intake.language)
        entry = {**check, "rationale": opt.rationale}
        (verified if check["ok"] else dropped).append(entry)
    # Time preference policy (deterministic): if any valid option is inside the member's
    # window, drop the ones outside it; otherwise keep them, marked as alternatives.
    outside_pref = False
    if window and verified:
        lo, hi = sch.to_min(window[0]), sch.to_min(window[1])
        inside = [o for o in verified if lo <= sch.to_min(o["start_time"]) <= hi]
        if inside:
            for o in verified:
                if o not in inside:
                    dropped.append({**o, "ok": False, "problems": [f"Outside the member's requested time {window[0]}–{window[1]}."]})
            verified = inside
        else:
            outside_pref = True
            for o in verified:
                o["warnings"] = o.get("warnings", []) + [f"Outside the member's requested time {window[0]}–{window[1]}."]
    recommendation = {
        "outcome": rec.outcome, "options": verified, "dropped_options": dropped,
        "missing_information": rec.missing_information, "notes_for_admin": rec.notes_for_admin,
        "verified_by": "rules engine (check_slot) after the Scheduling Agent returned",
        "time_window": list(window) if window else None, "outside_time_preference": outside_pref, "profile": profile,
    }
    if verified:
        status, msg = "pending_review", _options_message(len(verified))
        if outside_pref:
            msg += " None matched your preferred time exactly, so these are the closest available."
    elif rec.outcome == "needs_info" and rec.missing_information:
        status = "needs_info"
        msg = "To check availability we still need: " + "; ".join(rec.missing_information)[:350] + "."
        if defended:  # D3 also covers the Scheduling Agent's member-facing text
            filtered, reasons = dfn.filter_member_text(msg)
            if reasons:
                _flag(conn, request_id, "output_filtered", reasons)
            msg = filtered or "To check availability the temple office needs a few more details from you."
    else:
        status = "pending_review"
        msg = ("We couldn't find an open time that matches your request. The temple office will review it "
               "and contact you with alternatives. Nothing is booked yet.")
    _set(conn, request_id, status=status, recommendation_json=json.dumps(recommendation), member_message=msg)
    audit(conn, "system", f"status_{status}", request_id=request_id,
          details={"verified_options": len(verified), "dropped_options": len(dropped)})


def _flag(conn, request_id: str, key: str, value, layer: str = "D3") -> None:
    row = conn.execute("SELECT risk_flags FROM service_requests WHERE id = ?", (request_id,)).fetchone()
    flags = json.loads(row["risk_flags"]) if row and row["risk_flags"] else {}
    flags[key] = value
    conn.execute("UPDATE service_requests SET risk_flags = ? WHERE id = ?", (json.dumps(flags), request_id))
    audit(conn, "system", key, request_id=request_id, details={"layer": layer, "reasons": value})


def append_member_reply(conn, *, request_id: str, member_id: str, text: str, defenses: bool | None = None) -> None:
    req = conn.execute("SELECT * FROM service_requests WHERE id = ? AND member_id = ?", (request_id, member_id)).fetchone()
    if not req:
        raise WorkflowError(404, "Request not found.")
    if req["status"] != "needs_info":
        raise WorkflowError(409, "This request is not waiting for more information.")
    if dfn.enabled() if defenses is None else defenses:
        text, _ = dfn.sanitize(text)
        hits = dfn.screen(text)
        if hits:
            _flag(conn, request_id, "injection_patterns_in_reply", hits, layer="D2")
    combined = f"{req['raw_text']}\n\nFollow-up from member: {text}"
    if len(combined) > 4000:
        raise WorkflowError(422, "This request has grown too long. Please submit a new request.")
    _set(conn, request_id, raw_text=combined, status="processing", member_message=None)
    audit(conn, f"member:{member_id}", "member_replied", request_id=request_id, details={"chars": len(text)})


def create_slot_request(conn, *, member_id: str, service_id: str, date_str: str, start_time: str) -> str:
    """Fixed-slot services: the member picked an exact time, so no AI is needed. The
    rules engine assigns the first free qualified priest; the office still approves."""
    check_open_request_limit(conn, member_id)
    svc = sch.get_service_details(conn, service_id)
    if "error" in svc or svc["scheduling"] != "fixed_slots":
        raise WorkflowError(422, "That service does not use fixed time slots.")
    check = sch.first_free_priest(conn, service_id=service_id, date_str=date_str, start_time=start_time)
    if not check:
        raise WorkflowError(409, "That time is no longer available. Please pick another slot.")
    rid = new_id("req")
    ts = now_iso()
    recommendation = {"outcome": "options_found", "options": [{**check, "rationale": "Time chosen by the member in the slot picker."}],
                      "dropped_options": [], "missing_information": [],
                      "notes_for_admin": "Fixed-slot request picked by the member; priest assigned by the rules engine (no AI used).",
                      "verified_by": "rules engine (check_slot)"}
    intake = {"service_id": service_id, "preferred_dates": [date_str], "location_type": "temple",
              "summary": f"{svc['name']} on {date_str} at {start_time} (slot picker)"}
    conn.execute(
        """INSERT INTO service_requests (id, member_id, source, raw_text, status, intake_json, recommendation_json,
           missing_info, member_message, created_at, updated_at) VALUES (?,?, 'slot_picker', ?, 'pending_review', ?,?, '[]', ?,?,?)""",
        (rid, member_id, f"{svc['name']} — {date_str} {start_time}", json.dumps(intake), json.dumps(recommendation),
         "Your requested time is available. The temple office will confirm it; nothing is booked until then.", ts, ts))
    audit(conn, f"member:{member_id}", "request_submitted", request_id=rid, details={"source": "slot_picker"})
    return rid


# ---------------------------------------------------------------------------
# admin decisions (the only path that creates bookings)
# ---------------------------------------------------------------------------

APPROVABLE = ("pending_review", "needs_info", "failed")


def approve_request(conn, *, request_id: str, slot: dict, admin_name: str, note: str | None, edited: bool) -> dict:
    """Confirm a booking. Re-checks every rule inside an IMMEDIATE transaction, so two
    approvals can't both take the same priest/time."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        req = conn.execute("SELECT * FROM service_requests WHERE id = ?", (request_id,)).fetchone()
        if not req:
            raise WorkflowError(404, "Request not found.")
        if req["status"] not in APPROVABLE:
            raise WorkflowError(409, f"Request is already {req['status']}; it cannot be approved again.")
        if conn.execute("SELECT 1 FROM bookings WHERE request_id = ?", (request_id,)).fetchone():
            raise WorkflowError(409, "A booking already exists for this request.")
        check = sch.check_slot(conn, service_id=slot["service_id"], priest_id=slot["priest_id"],
                               date_str=slot["date"], start_time=slot["start_time"],
                               location_type=slot["location_type"], city=slot.get("city"),
                               language=slot.get("language"))
        if not check["ok"]:
            raise WorkflowError(409, "This slot no longer passes the scheduling rules.", check["problems"])
        bid = new_id("bk")
        conn.execute(
            """INSERT INTO bookings (id, request_id, member_id, service_id, priest_id, date, start_time, end_time,
               location_type, city, language, base_price_cents, travel_fee_cents, total_cents, status, payment,
               approved_by, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'confirmed', 'unpaid', ?, ?)""",
            (bid, request_id, req["member_id"], check["service_id"], check["priest_id"], check["date"],
             check["start_time"], check["end_time"], check["location_type"], sch.norm_city(slot.get("city")),
             check["language"], check["base_price_cents"], check["travel_fee_cents"], check["total_cents"],
             admin_name, now_iso()))
        msg = (f"Confirmed: {check['service_name']} on {check['date']} at {check['start_time']} with "
               f"{check['priest_name']}. Total ${check['total_cents'] / 100:.2f} (payment is arranged with the office; "
               "no online payment in this demo).")
        _set(conn, request_id, status="approved", booking_id=bid, admin_note=note, member_message=msg)
        conn.execute("INSERT INTO approvals (request_id, decision, admin_name, note, slot_json, decided_at) VALUES (?,?,?,?,?,?)",
                     (request_id, "approved_edited" if edited else "approved", admin_name, note, json.dumps(slot), now_iso()))
        audit(conn, f"admin:{admin_name}", "booking_approved", request_id=request_id, booking_id=bid,
              details={"edited": edited, "slot": slot, "total_cents": check["total_cents"]})
        conn.execute("COMMIT")
        return {"booking_id": bid, "check": check}
    except WorkflowError as exc:
        conn.execute("ROLLBACK")
        _log_blocked(conn, request_id, admin_name, slot, exc)
        raise
    except sqlite3.IntegrityError as exc:
        conn.execute("ROLLBACK")
        err = WorkflowError(409, "Booking blocked by a database constraint (duplicate or overlapping booking).", str(exc))
        _log_blocked(conn, request_id, admin_name, slot, err)
        raise err from exc
    except Exception:
        conn.execute("ROLLBACK")
        raise


def _log_blocked(conn, request_id, admin_name, slot, exc: WorkflowError) -> None:
    if exc.status_code == 404:
        return
    conn.execute("INSERT INTO approvals (request_id, decision, admin_name, note, slot_json, decided_at) VALUES (?,?,?,?,?,?)",
                 (request_id, "blocked", admin_name, exc.message, json.dumps(slot), now_iso()))
    audit(conn, f"admin:{admin_name}", "approval_blocked", request_id=request_id,
          details={"reason": exc.message, "problems": exc.details, "slot": slot})


def decide_request(conn, *, request_id: str, decision: str, admin_name: str, message: str) -> None:
    """Reject, or send back to the member asking for more information."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        req = conn.execute("SELECT status FROM service_requests WHERE id = ?", (request_id,)).fetchone()
        if not req:
            raise WorkflowError(404, "Request not found.")
        if req["status"] not in APPROVABLE:
            raise WorkflowError(409, f"Request is already {req['status']}.")
        if decision == "rejected":
            _set(conn, request_id, status="rejected", admin_note=message,
                 member_message=f"The temple office could not accommodate this request: {message}")
        else:
            _set(conn, request_id, status="needs_info", admin_note=message, member_message=message)
        conn.execute("INSERT INTO approvals (request_id, decision, admin_name, note, decided_at) VALUES (?,?,?,?,?)",
                     (request_id, decision, admin_name, message, now_iso()))
        audit(conn, f"admin:{admin_name}", f"request_{decision}", request_id=request_id, details={"message": message})
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def cancel_booking(conn, *, booking_id: str, admin_name: str, reason: str) -> None:
    conn.execute("BEGIN IMMEDIATE")
    try:
        b = conn.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,)).fetchone()
        if not b:
            raise WorkflowError(404, "Booking not found.")
        if b["status"] != "confirmed":
            raise WorkflowError(409, f"Booking is already {b['status']}.")
        conn.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
        if b["request_id"]:
            _set(conn, b["request_id"], status="cancelled", admin_note=f"Cancelled: {reason}",
                 member_message=f"Your booking was cancelled by the temple office: {reason}")
        audit(conn, f"admin:{admin_name}", "booking_cancelled", request_id=b["request_id"], booking_id=booking_id,
              details={"reason": reason})
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
