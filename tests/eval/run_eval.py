"""Run the SERVE evaluation set through the real agents (gpt-6-luna via Portkey).

Each case gets a fresh copy of the seeded demo database, goes through the same
pipeline the app uses (Intake Agent -> code checks -> Scheduling Agent -> rules
engine re-verification), and is scored against tests/eval/cases.py.

    .venv/bin/python -m tests.eval.run_eval --validate-only          # oracle check, no model calls
    .venv/bin/python -m tests.eval.run_eval --label baseline_phase1  # real model calls
    .venv/bin/python -m tests.eval.run_eval --label v2_optimized --profile optimized

Outputs evidence/eval/<label>.json and evidence/eval/<label>.md. Failed cases are
kept as-is; expected answers are never edited after a run.
"""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import shutil
import statistics
import time
from datetime import date, timedelta
from pathlib import Path

from backend import config, db, pipeline, scheduling as sch
from tests.eval.cases import CASES
from tests.eval.heldout_cases import HELDOUT

SETS = {"main": CASES, "heldout": HELDOUT}

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evidence" / "eval"
WORK = ROOT / "backend" / "data" / "eval"

# ---------------------------------------------------------------------------
# date tokens
# ---------------------------------------------------------------------------

def _first(wd: int, min_ahead: int, today: date) -> date:
    d = today + timedelta(days=min_ahead)
    return d + timedelta(days=(wd - d.weekday()) % 7)


def resolve_tokens(conn) -> dict[str, date]:
    t = db.today()
    off = conn.execute("SELECT start_date, end_date FROM priest_time_off WHERE priest_id='pr_iyer'").fetchone()
    s, e = date.fromisoformat(off[0]), date.fromisoformat(off[1])
    last_sun = t - timedelta(days=(t.weekday() - 6) % 7 or 7)
    return {
        "SAT_NEXT": _first(5, 1, t), "SAT2": _first(5, 14, t), "SAT3": _first(5, 21, t),
        "SUN1": _first(6, 7, t), "SUN2": _first(6, 14, t), "MON1": _first(0, 7, t), "TUE1": _first(1, 7, t),
        "THU1": _first(3, 7, t), "FRI1": _first(4, 7, t), "TOMORROW": t + timedelta(days=1),
        "LAST_SUNDAY": last_sun,
        "DIWALI": date.fromisoformat(conn.execute("SELECT date FROM events WHERE id='evt_diwali'").fetchone()[0]),
        "IYER_OFF_MID": s + (e - s) / 2,
    }


def words(d: date) -> str:
    return f"{d.strftime('%A, %B')} {d.day}"


def ordinal(n: int) -> str:
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def render(text: str, tok: dict[str, date]) -> str:
    for k, v in tok.items():
        text = text.replace("{" + k + "_ORD}", ordinal(v.day))
        text = text.replace("{" + k + "_WORDS_UPPER}", words(v).upper())
        text = text.replace("{" + k + "_WORDS}", words(v))
    for k, v in tok.items():
        text = text.replace("{" + k + "}", "tomorrow" if k == "TOMORROW" else words(v))
    return text


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------

def norm(v):
    return v.strip().lower() if isinstance(v, str) else v


def time_category(intake: dict) -> str:
    if "time_preference" in intake:  # v2 schema
        return intake.get("time_preference") or "any"
    return intake.get("time_of_day") or "any"  # Phase 1 schema


def to_min(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def score_case(case: dict, tok: dict, req: dict, intake: dict | None, rec: dict | None, missing: list) -> dict:
    exp, sch_exp = case["expect"], case["schedule"]
    fields: dict[str, bool] = {}
    intake = intake or {}
    if "status" in exp:
        fields["status"] = req["status"] == exp["status"]
    if "service_id" in exp:
        fields["service_id"] = intake.get("service_id") == exp["service_id"]
    if "dates" in exp:
        fields["dates"] = set(intake.get("preferred_dates") or []) == {tok[x].isoformat() for x in exp["dates"]}
    if "location_type" in exp:
        fields["location_type"] = intake.get("location_type") == exp["location_type"]
    if "city" in exp:
        fields["city"] = norm(sch.norm_city(intake.get("city"))) == exp["city"]
    if "language" in exp:
        fields["language"] = norm(intake.get("language")) == exp["language"]
    if "attendees" in exp:
        fields["attendees"] = intake.get("attendees") == exp["attendees"]
    if "time" in exp:
        allowed = exp["time"] if isinstance(exp["time"], list) else [exp["time"]]
        fields["time"] = time_category(intake) in allowed
    if "missing" in exp:
        fields["missing"] = set(missing or []) == set(exp["missing"])
    if "special_contains" in exp:
        sr = " ".join(intake.get("special_requirements") or []).lower()
        fields["special_requirements"] = all(k in sr for k in exp["special_contains"])

    options = (rec or {}).get("options", [])
    dropped = (rec or {}).get("dropped_options", [])
    problems: list[str] = []
    req_dates = {tok[x].isoformat() for x in exp.get("dates", [])}
    for o in options:
        tag = f"{o.get('priest_id')} {o.get('date')} {o.get('start_time')}"
        if sch_exp.get("window"):
            lo, hi = sch_exp["window"]
            if not (to_min(lo) <= to_min(o["start_time"]) <= to_min(hi)):
                problems.append(f"{tag}: outside window {lo}-{hi}")
        if sch_exp.get("allowed_priests") and o["priest_id"] not in sch_exp["allowed_priests"]:
            problems.append(f"{tag}: priest not allowed")
        if o["priest_id"] in sch_exp.get("forbidden_priests", []):
            problems.append(f"{tag}: forbidden priest")
        if o["date"] in {tok[x].isoformat() for x in sch_exp.get("forbid_dates", [])}:
            problems.append(f"{tag}: forbidden date")
        if sch_exp.get("forbid_after"):
            d, t = sch_exp["forbid_after"]
            if o["date"] == tok[d].isoformat() and to_min(o["start_time"]) >= to_min(t):
                problems.append(f"{tag}: during blocked event time")
        if sch_exp.get("total_cents") is not None and o["total_cents"] != sch_exp["total_cents"]:
            problems.append(f"{tag}: total {o['total_cents']} != {sch_exp['total_cents']}")
        if sch_exp.get("dates_strict", True) and req_dates and o["date"] not in req_dates:
            problems.append(f"{tag}: not on requested date")
    eo = sch_exp.get("expect_options")
    if eo is True and not options:
        problems.append("expected at least one valid option, got none")
    if eo is False and options:
        problems.append(f"expected no option, got {len(options)}")
    schedule_ok = not problems
    return {
        "fields": fields,
        "fields_correct": sum(fields.values()), "fields_total": len(fields),
        "schedule_ok": schedule_ok, "schedule_problems": problems,
        "option_count": len(options), "agent_proposals_rejected_by_rules": len(dropped),
        "pass": all(fields.values()) and schedule_ok,
    }


# ---------------------------------------------------------------------------
# oracle validation of the expected scheduling outcomes (no model)
# ---------------------------------------------------------------------------

def validate(conn, tok, cases=None) -> list[str]:
    issues = []
    for c in cases or CASES:
        exp, se = c["expect"], c["schedule"]
        if exp.get("status") != "pending_review" or se.get("expect_options") is None:
            continue
        city = exp.get("city")
        slots = []
        for dtok in exp["dates"]:
            r = sch.search_available_slots(conn, service_id=exp["service_id"], date_str=tok[dtok].isoformat(),
                                           location_type=exp["location_type"], city=city,
                                           language=exp.get("language"), limit=500, per_priest=500)
            slots += r.get("slots", [])
        ok = []
        for s in slots:
            if se.get("window") and not (to_min(se["window"][0]) <= to_min(s["start_time"]) <= to_min(se["window"][1])):
                continue
            if se.get("allowed_priests") and s["priest_id"] not in se["allowed_priests"]:
                continue
            if s["priest_id"] in se.get("forbidden_priests", []):
                continue
            ok.append(s)
        if se["expect_options"] and not ok:
            issues.append(f"{c['id']}: expected options but the rules engine finds none")
        if se["expect_options"] is False and ok:
            issues.append(f"{c['id']}: expected no options but rules engine finds {len(ok)}")
        if se.get("total_cents") and any(s["total_cents"] != se["total_cents"] for s in ok):
            issues.append(f"{c['id']}: total mismatch")
    return issues


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------

async def run_case(case, tok, template: Path, run_kwargs: dict) -> dict:
    path = template.parent / f"{case['id']}.db"
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(path) + suffix)
        if p.exists():
            p.unlink()
    shutil.copy(template, path)
    db.DB_PATH = path
    conn = db.connect()
    text = render(case["text"], tok)
    rid = pipeline.create_ai_request(conn, member_id=config.DEMO_MEMBER_ID, text=text, source="ai_request")
    t0 = time.perf_counter()
    await pipeline.process_request(rid, **run_kwargs)
    wall = time.perf_counter() - t0
    req = dict(conn.execute("SELECT * FROM service_requests WHERE id=?", (rid,)).fetchone())
    runs = [dict(r) for r in conn.execute("SELECT * FROM agent_runs WHERE request_id=? ORDER BY started_at", (rid,))]
    tools = [dict(r) for r in conn.execute("SELECT agent, tool_name, args_json, ok FROM tool_calls WHERE request_id=? ORDER BY id", (rid,))]
    bookings = conn.execute("SELECT COUNT(*) FROM bookings WHERE request_id=?", (rid,)).fetchone()[0]
    conn.close()
    intake = json.loads(req["intake_json"]) if req["intake_json"] else None
    rec = json.loads(req["recommendation_json"]) if req["recommendation_json"] else None
    missing = json.loads(req["missing_info"]) if req["missing_info"] else []
    s = score_case(case, tok, req, intake, rec, missing)
    usage = {k: sum((r.get(k) or 0) for r in runs) for k in
             ("input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens", "reasoning_tokens",
              "model_requests", "tool_calls")}
    usage["cost_usd"] = round(sum((r.get("cost_usd") or 0) for r in runs), 8)
    usage["portkey_cache_hits"] = sum((r.get("portkey_cache_hits") or 0) for r in runs)
    return {
        "id": case["id"], "category": case["category"], "text": text, "status": req["status"],
        "error": req["error"], "member_message": req["member_message"], **s,
        "critical_bookings_created": bookings,
        "intake": intake, "options": [{k: o.get(k) for k in ("priest_id", "date", "start_time", "location_type", "city",
                                                             "language", "total_cents")} for o in (rec or {}).get("options", [])],
        "dropped": [{"proposal": f"{o.get('priest_id')} {o.get('date')} {o.get('start_time')}", "problems": o.get("problems")}
                    for o in (rec or {}).get("dropped_options", [])],
        "notes_for_admin": (rec or {}).get("notes_for_admin"),
        "wall_seconds": round(wall, 2), "usage": usage,
        "runs": [{k: r.get(k) for k in ("agent", "status", "error", "response_model", "latency_ms", "model_requests",
                                        "input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens",
                                        "tool_calls", "cost_usd", "provider", "portkey_target", "portkey_cache",
                                        "portkey_cache_hits")} for r in runs],
        "tool_sequence": [f"{t['agent']}:{t['tool_name']}" for t in tools],
    }


def summarize(label: str, results: list[dict], meta: dict) -> dict:
    n = len(results)
    field_names = sorted({f for r in results for f in r["fields"]})
    by_field = {}
    for f in field_names:
        scored = [r["fields"][f] for r in results if f in r["fields"]]
        by_field[f] = {"correct": sum(scored), "total": len(scored), "accuracy": round(sum(scored) / len(scored), 3)}
    tot_fields = sum(r["fields_total"] for r in results)
    walls = [r["wall_seconds"] for r in results]
    costs = [r["usage"]["cost_usd"] for r in results]
    sched_cases = [r for r in results if r["status"] == "pending_review"]
    return {
        "label": label, **meta, "cases": n,
        "cases_passed": sum(r["pass"] for r in results),
        "field_accuracy_overall": round(sum(r["fields_correct"] for r in results) / tot_fields, 3),
        "field_accuracy_by_field": by_field,
        "schedule_correct": sum(r["schedule_ok"] for r in results),
        "final_options_total": sum(r["option_count"] for r in results),
        "agent_proposals_rejected_by_rules": sum(r["agent_proposals_rejected_by_rules"] for r in results),
        "cases_with_option_policy_violations": sum(1 for r in results if any("outside" in p or "forbidden" in p or "priest not allowed" in p or "blocked" in p for p in r["schedule_problems"])),
        "critical_bookings_created_by_agents": sum(r["critical_bookings_created"] for r in results),
        "pipeline_errors": sum(1 for r in results if r["status"] == "failed"),
        "latency_seconds": {"mean": round(statistics.mean(walls), 2), "median": round(statistics.median(walls), 2),
                            "p90": round(sorted(walls)[int(0.9 * (n - 1))], 2), "max": round(max(walls), 2)},
        "tokens": {k: sum(r["usage"][k] for r in results) for k in
                   ("input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens", "reasoning_tokens",
                    "model_requests", "tool_calls", "portkey_cache_hits")},
        "cost_usd_total": round(sum(costs), 6),
        "cost_usd_per_request_mean": round(statistics.mean(costs), 6),
        "cost_usd_per_scheduled_request_mean": round(statistics.mean([r["usage"]["cost_usd"] for r in sched_cases]), 6) if sched_cases else None,
        "failed_cases": [r["id"] for r in results if not r["pass"]],
    }


def write_md(summary: dict, results: list[dict], path: Path) -> None:
    s = summary
    lines = [f"# Evaluation: {s['label']}", "", f"- Run at: {s['run_at']}  ·  model requested: `{s['model']}`  ·  profile: `{s['profile']}`",
             f"- Cases passed (all fields + scheduling correct): **{s['cases_passed']}/{s['cases']}**",
             f"- Field accuracy overall: **{s['field_accuracy_overall']:.1%}**  ·  scheduling correct: **{s['schedule_correct']}/{s['cases']}**",
             f"- Agent proposals rejected by rules engine: {s['agent_proposals_rejected_by_rules']}  ·  bookings created by agents: {s['critical_bookings_created_by_agents']}  ·  pipeline errors: {s['pipeline_errors']}",
             f"- Latency per request (s): mean {s['latency_seconds']['mean']}, median {s['latency_seconds']['median']}, p90 {s['latency_seconds']['p90']}, max {s['latency_seconds']['max']}",
             f"- Tokens: input {s['tokens']['input_tokens']:,} (cached {s['tokens']['cached_input_tokens']:,}, cache-write {s['tokens']['cache_write_tokens']:,}), output {s['tokens']['output_tokens']:,}; model requests {s['tokens']['model_requests']}, tool calls {s['tokens']['tool_calls']}",
             f"- Cost (list price): total ${s['cost_usd_total']:.6f}, mean per request ${s['cost_usd_per_request_mean']:.6f}",
             "", "## Field accuracy", "", "| Field | Correct | Total | Accuracy |", "|---|---|---|---|"]
    for f, v in s["field_accuracy_by_field"].items():
        lines.append(f"| {f} | {v['correct']} | {v['total']} | {v['accuracy']:.0%} |")
    lines += ["", "## Cases", "", "| Case | Status | Fields | Schedule | Options | Cost | Seconds | Problems |", "|---|---|---|---|---|---|---|---|"]
    for r in results:
        wrong = [f for f, ok in r["fields"].items() if not ok]
        probs = "; ".join(([f"wrong: {', '.join(wrong)}"] if wrong else []) + r["schedule_problems"])[:220]
        lines.append(f"| {'✅' if r['pass'] else '❌'} {r['id']} | {r['status']} | {r['fields_correct']}/{r['fields_total']} | "
                     f"{'ok' if r['schedule_ok'] else 'fail'} | {r['option_count']} | ${r['usage']['cost_usd']:.5f} | {r['wall_seconds']} | {probs} |")
    path.write_text("\n".join(lines) + "\n")


async def main(label: str | None, profile: str | None, only: list[str] | None, validate_only: bool,
               case_set: str = "main"):
    cases_all = SETS[case_set]
    work = WORK / (label or "_validate")
    work.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    template = work / "_template.db"
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(template) + suffix)
        if p.exists():
            p.unlink()
    db.DB_PATH = template
    db.init_db()
    conn = db.connect()
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    tok = resolve_tokens(conn)
    issues = validate(conn, tok, cases_all)
    conn.close()
    print("Oracle check of expected scheduling outcomes:", "OK" if not issues else issues)
    if validate_only or issues:
        return
    sig = inspect.signature(pipeline.process_request)
    run_kwargs = {"profile": profile} if profile and "profile" in sig.parameters else {}
    if profile and not run_kwargs:
        raise SystemExit("This code version does not support --profile.")
    cases = [c for c in cases_all if not only or c["id"] in only]
    results = []
    log = OUT / f"{label}.log"
    log.write_text("")
    for c in cases:
        r = await run_case(c, tok, template, run_kwargs)
        with log.open("a") as fh:
            fh.write(json.dumps(r, default=str) + "\n")  # raw per-case record, written before scoring summary
        results.append(r)
        print(f"{'PASS' if r['pass'] else 'FAIL'} {r['id']:34} {r['status']:15} fields {r['fields_correct']}/{r['fields_total']} "
              f"sched {'ok' if r['schedule_ok'] else 'FAIL'} ${r['usage']['cost_usd']:.5f} {r['wall_seconds']}s "
              + ("" if r["pass"] else str([f for f, ok in r["fields"].items() if not ok] + r["schedule_problems"])[:200]))
    meta = {"run_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": config.MODEL_NAME, "case_set": case_set,
            "profile": profile or getattr(pipeline, "default_profile", lambda: "phase1")(),
            "defenses": __import__("os").getenv("SERVE_DEFENSES", "on"),
            "eval_today": db.today().isoformat(), "date_tokens": {k: v.isoformat() for k, v in tok.items()},
            "pricing": json.loads(config.PRICES_PATH.read_text())}
    summary = summarize(label, results, meta)
    (OUT / f"{label}.json").write_text(json.dumps({"summary": summary, "results": results}, indent=2, default=str))
    write_md(summary, results, OUT / f"{label}.md")
    print(json.dumps({k: summary[k] for k in ("cases_passed", "cases", "field_accuracy_overall", "schedule_correct",
                                              "cost_usd_total", "latency_seconds", "failed_cases")}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--label")
    ap.add_argument("--profile")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--validate-only", action="store_true")
    ap.add_argument("--set", default="main", choices=list(SETS))
    a = ap.parse_args()
    if not a.validate_only and not a.label:
        ap.error("--label is required unless --validate-only")
    asyncio.run(main(a.label, a.profile, a.only, a.validate_only, a.set))
