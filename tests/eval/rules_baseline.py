"""Rules-only baseline (no AI): keyword/regex parser + the same rules engine.

Answers "what would a non-AI automation get on the same 27 cases?" Scored with the
same scorer as the agents. Caveat: written by the same author who wrote the test
cases, so it is likely an optimistic upper bound for a keyword parser on these texts.

    .venv/bin/python -m tests.eval.rules_baseline
"""

from __future__ import annotations

import json
import re
import statistics
import time
from datetime import date, timedelta

from backend import db, scheduling as sch
from backend.agents import IntakeResult, deterministic_missing
from tests.eval.cases import CASES
from tests.eval.run_eval import OUT, WORK, render, resolve_tokens, score_case

MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
LANGS = ["hindi", "telugu", "tamil", "gujarati", "sanskrit", "english", "bengali", "marathi", "kannada", "punjabi"]
SPECIAL = ["wheelchair", "walker", "accessible", "elderly", "chair", "allergy", "vegetarian", "memory of"]


def parse_time(t: str):
    if "late morning" in t:
        return "late_morning", None, None
    m = re.search(r"between (\d{1,2})(?::(\d{2}))? and (\d{1,2})(?::(\d{2}))?\s*(am|pm)?", t)
    if m:
        h1, m1, h2, m2, ap = int(m[1]), m[2] or "00", int(m[3]), m[4] or "00", m[5]
        if ap == "pm" and h2 < 12:
            h1, h2 = h1 + (12 if h1 < 12 else 0), h2 + 12
        return "range", f"{h1:02d}:{m1}", f"{h2:02d}:{m2}"
    m = re.search(r"\bat (\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", t) or re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", t)
    if m:
        h = int(m[1]) % 12 + (12 if m[3] == "pm" else 0)
        return "exact", f"{h:02d}:{m[2] or '00'}", None
    for k in ("morning", "afternoon", "evening"):
        if k in t:
            return k, None, None
    return "any", None, None


def parse(text: str, conn) -> IntakeResult:
    t = text.lower()
    svc_id = None
    for r in conn.execute("SELECT id, name, aliases FROM services"):
        names = [r["name"].lower()] + [a.lower() for a in json.loads(r["aliases"])]
        if any(n in t for n in names):
            svc_id = r["id"]
            break
    today = db.today()
    dates = []
    for m in re.finditer(r"(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday),? (" + "|".join(MONTHS) + r") (\d{1,2})", t):
        d = date(today.year, MONTHS[m[1]], int(m[2]))
        if d < today - timedelta(days=200):
            d = d.replace(year=today.year + 1)
        dates.append(d.isoformat())
    if "sorry, i meant" in t and len(dates) > 1:
        dates = dates[-1:]
    if "tomorrow" in t:
        dates.append((today + timedelta(days=1)).isoformat())
    loc = "home" if re.search(r"\b(home|house)\b", t) else "temple" if re.search(r"\b(temple|hall)\b", t) else None
    city = None
    for z in conn.execute("SELECT city FROM travel_zones ORDER BY length(city) DESC"):
        if re.search(r"\b" + re.escape(z["city"]) + r"\b", t):
            city = z["city"]
            break
    lang = next((l.capitalize() for l in LANGS if l in t), None)
    m = re.search(r"(\d+)\s+(guests|people|family members|relatives)", t)
    pref, lo, hi = parse_time(t)
    intake = IntakeResult(is_service_request=svc_id is not None or bool(dates), service_id=svc_id,
                          service_match_reason="keyword match", preferred_dates=dates, time_preference=pref,
                          earliest_start=lo, latest_start=hi, location_type=loc, city=city, language=lang,
                          attendees=int(m[1]) if m else None,
                          special_requirements=[k for k in SPECIAL if k in t], summary=text[:100])
    svc = sch.get_service_details(conn, svc_id) if svc_id else None
    if svc and svc["location_mode"] != "either":
        intake.location_type = svc["location_mode"]
    if intake.location_type == "temple":
        intake.city = None
    if intake.location_type == "home" and not intake.city:
        intake.city = conn.execute("SELECT home_city FROM members WHERE id='mem_arjun_patel'").fetchone()[0]
    return intake


def main():
    conn = db.connect() if False else None
    db.DB_PATH = WORK / "_template.db"
    conn = db.connect()
    tok = resolve_tokens(conn)
    results = []
    for c in CASES:
        t0 = time.perf_counter()
        text = render(c["text"], tok)
        intake = parse(text, conn)
        window = sch.time_window(intake.time_preference, intake.earliest_start, intake.latest_start)
        missing = deterministic_missing(intake, conn)
        options = []
        if not missing:
            for d in intake.preferred_dates:
                r = sch.search_available_slots(conn, service_id=intake.service_id, date_str=d,
                                               location_type=intake.location_type, city=intake.city,
                                               language=intake.language,
                                               earliest_start=window[0] if window else None,
                                               latest_start=window[1] if window else None, limit=3)
                options += [{**s, "ok": True} for s in r.get("slots", [])]
            options = options[:3]
        status = "needs_info" if missing else "pending_review"
        req = {"status": status}
        s = score_case(c, tok, req, intake.model_dump(), {"options": options, "dropped_options": []}, missing)
        results.append({"id": c["id"], "status": status, **s, "ms": round((time.perf_counter() - t0) * 1000, 1),
                        "intake": intake.model_dump(), "options": options})
        print(f"{'PASS' if s['pass'] else 'FAIL'} {c['id']:34} fields {s['fields_correct']}/{s['fields_total']} "
              f"sched {'ok' if s['schedule_ok'] else 'FAIL'} " + ("" if s["pass"] else str([f for f, ok in s["fields"].items() if not ok] + s["schedule_problems"])[:160]))
    tot = sum(r["fields_total"] for r in results)
    summary = {"label": "rules_only_baseline", "cases": len(results), "cases_passed": sum(r["pass"] for r in results),
               "field_accuracy_overall": round(sum(r["fields_correct"] for r in results) / tot, 3),
               "schedule_correct": sum(r["schedule_ok"] for r in results),
               "field_accuracy_by_field": {f: round(statistics.mean([r["fields"][f] for r in results if f in r["fields"]]), 3)
                                           for f in sorted({f for r in results for f in r["fields"]})},
               "mean_ms": round(statistics.mean(r["ms"] for r in results), 1), "cost_usd": 0.0,
               "failed_cases": [r["id"] for r in results if not r["pass"]],
               "caveat": "Keyword parser written by the test author after seeing the cases; optimistic upper bound."}
    (OUT / "rules_only_baseline.json").write_text(json.dumps({"summary": summary, "results": results}, indent=2, default=str))
    print(json.dumps({k: summary[k] for k in ("cases_passed", "cases", "field_accuracy_overall", "schedule_correct", "mean_ms")}))


if __name__ == "__main__":
    main()
