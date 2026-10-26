"""Run the frozen rules-only parser (tests/eval/rules_baseline.py, unchanged) on the held-out set."""

import json
import statistics

from backend import db, scheduling as sch
from backend.agents import deterministic_missing
from tests.eval.heldout_cases import HELDOUT
from tests.eval.rules_baseline import parse
from tests.eval.run_eval import OUT, WORK, render, resolve_tokens, score_case

db.DB_PATH = WORK / "_template.db"
conn = db.connect()
tok = resolve_tokens(conn)
results = []
for c in HELDOUT:
    text = render(c["text"], tok)
    intake = parse(text, conn)
    window = sch.time_window(intake.time_preference, intake.earliest_start, intake.latest_start)
    missing = deterministic_missing(intake, conn)
    options = []
    if not missing:
        for d in intake.preferred_dates:
            r = sch.search_available_slots(conn, service_id=intake.service_id, date_str=d, location_type=intake.location_type,
                                           city=intake.city, language=intake.language,
                                           earliest_start=window[0] if window else None,
                                           latest_start=window[1] if window else None, limit=3)
            options += r.get("slots", [])
        options = options[:3]
    status = "needs_info" if missing else "pending_review"
    s = score_case(c, tok, {"status": status}, intake.model_dump(), {"options": options, "dropped_options": []}, missing)
    results.append({"id": c["id"], "text": text, "status": status, **s, "intake": intake.model_dump()})
    print(f"{'PASS' if s['pass'] else 'FAIL'} {c['id']:30} fields {s['fields_correct']}/{s['fields_total']} sched {'ok' if s['schedule_ok'] else 'FAIL'} "
          + ("" if s["pass"] else str([f for f, ok in s["fields"].items() if not ok] + s["schedule_problems"])[:150]))
tot = sum(r["fields_total"] for r in results)
summary = {"label": "rules_only_heldout", "cases": len(results), "cases_passed": sum(r["pass"] for r in results),
           "field_accuracy_overall": round(sum(r["fields_correct"] for r in results) / tot, 3),
           "schedule_correct": sum(r["schedule_ok"] for r in results),
           "field_accuracy_by_field": {f: round(statistics.mean([r["fields"][f] for r in results if f in r["fields"]]), 3)
                                       for f in sorted({f for r in results for f in r["fields"]})},
           "failed_cases": [r["id"] for r in results if not r["pass"]]}
(OUT / "rules_only_heldout.json").write_text(json.dumps({"summary": summary, "results": results}, indent=2, default=str))
print(json.dumps({k: summary[k] for k in ("cases_passed", "cases", "field_accuracy_overall", "schedule_correct")}))
