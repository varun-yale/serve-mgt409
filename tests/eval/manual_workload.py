"""Reproducible operational comparison: the scheduling workload behind each evaluation request.

For every case with a complete request (using the EXPECTED answers, not agent output), this
measures from the seeded database what a coordinator doing it by hand would have to check to
find valid options — the same rules SERVE's engine applies:
  - qualified priests to consider, and how many also speak the requested language
  - priest-day calendars to open (candidate priests x requested dates)
  - candidate start times to test, and individual rule checks (each candidate checked against
    qualification, language, lead time, hours, availability, time off, bookings, events, travel)
  - valid options that exist, and whether any exist at all
Counts are deterministic and reproducible. Converting them to minutes is an assumption and is
labelled as such; no real staff timing was collected.

    .venv/bin/python -m tests.eval.manual_workload
Writes evidence/impact/manual_workload.{json,md}
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

from backend import db, scheduling as sch
from tests.eval.cases import CASES
from tests.eval.heldout_cases import HELDOUT
from tests.eval.run_eval import WORK, resolve_tokens, to_min

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evidence" / "impact"
RULES_PER_CHECK = 9  # rule families evaluated by check_slot for every candidate


def workload(conn, case, tok):
    e = case["expect"]
    if e.get("status") != "pending_review" or not e.get("service_id") or not e.get("dates"):
        return None
    win = case["schedule"].get("window")
    svc = sch.get_service_details(conn, e["service_id"])
    priests = sch.find_qualified_priests(conn, e["service_id"], e.get("language"))
    lang_ok = [p for p in priests if p["speaks_requested_language"] in (None, True)]
    dates = [tok[d].isoformat() for d in e["dates"]]
    cands = (svc["fixed_start_times"] if svc["scheduling"] == "fixed_slots"
             else [sch.to_hhmm(m) for m in range(6 * 60 + 30, 20 * 60 + 1, 30)])
    if win:
        cands = [t for t in cands if to_min(win[0]) <= to_min(t) <= to_min(win[1])]
    checks, valid = 0, 0
    for p in lang_ok:
        for d in dates:
            for t in cands:
                checks += 1
                c = sch.check_slot(conn, service_id=e["service_id"], priest_id=p["priest_id"], date_str=d,
                                   start_time=t, location_type=e["location_type"], city=e.get("city"),
                                   language=e.get("language"))
                valid += c["ok"]
    return {"id": case["id"], "qualified_priests": len(priests), "qualified_and_language_ok": len(lang_ok),
            "calendars_to_open": len(lang_ok) * len(dates), "candidate_slots_to_test": checks,
            "rule_checks": checks * RULES_PER_CHECK, "travel_lookup": e["location_type"] == "home",
            "valid_options_exist": valid, "answer_is_no_availability": valid == 0}


def main():
    db.DB_PATH = WORK / "v2_optimized" / "_template.db"
    conn = db.connect()
    tok = resolve_tokens(conn)
    rows = [r for c in CASES + HELDOUT if (r := workload(conn, c, tok))]
    agg = {k: round(statistics.mean(r[k] for r in rows), 1) for k in
           ("qualified_priests", "qualified_and_language_ok", "calendars_to_open", "candidate_slots_to_test", "rule_checks")}
    summary = {
        "requests_analyzed": len(rows),
        "means_per_request": agg,
        "home_requests_needing_travel_lookup": sum(r["travel_lookup"] for r in rows),
        "requests_where_correct_answer_is_no_availability": sum(r["answer_is_no_availability"] for r in rows),
        "with_serve": "Agents + rules engine perform these checks automatically (measured ~10.5 s, $0.00056 per request, "
                      "optimized profile); the administrator reviews evidence and clicks Approve.",
        "minutes_estimate": {"label": "ESTIMATE (assumption, not measured)",
                             "assumption": "1 minute per priest-day calendar opened + 0.25 min per candidate slot tested + 3 min travel lookup if home + 4 min read/reply",
                             "mean_minutes": round(statistics.mean(
                                 r["calendars_to_open"] * 1 + r["candidate_slots_to_test"] * 0.25 + (3 if r["travel_lookup"] else 0) + 4
                                 for r in rows), 1)},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manual_workload.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))
    md = ["# Scheduling workload behind each request (deterministic, reproducible)", "",
          f"Requests analyzed: {len(rows)} (complete requests from the 27 main + 15 held-out cases; expected answers used).", "",
          "| Mean per request | Value |", "|---|---|"] + [f"| {k.replace('_', ' ')} | {v} |" for k, v in agg.items()] + [
          f"| home requests needing a travel lookup | {summary['home_requests_needing_travel_lookup']} of {len(rows)} |",
          f"| requests whose correct answer is 'no availability' | {summary['requests_where_correct_answer_is_no_availability']} of {len(rows)} |", "",
          f"**With SERVE:** {summary['with_serve']}", "",
          f"**{summary['minutes_estimate']['label']}:** {summary['minutes_estimate']['assumption']} → mean ≈ {summary['minutes_estimate']['mean_minutes']} min per request.", "",
          "| Case | Qualified priests | + language | Calendars | Candidate slots | Rule checks | Valid options |", "|---|---|---|---|---|---|---|"]
    md += [f"| {r['id']} | {r['qualified_priests']} | {r['qualified_and_language_ok']} | {r['calendars_to_open']} | {r['candidate_slots_to_test']} | {r['rule_checks']} | {r['valid_options_exist']} |" for r in rows]
    (OUT / "manual_workload.md").write_text("\n".join(md) + "\n")
    print("\n".join(md[:14]))


if __name__ == "__main__":
    main()
