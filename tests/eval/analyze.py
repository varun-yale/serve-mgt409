"""Tokenomics, cost projections and operational-impact analysis from saved evidence.

Reads only result files written by real runs (no model calls):
  evidence/eval/baseline_phase1.json, v2_standard.json, v2_optimized.json,
  evidence/eval/heldout_<profile>.json, rules_only_baseline.json, rules_only_heldout.json
Writes evidence/tokenomics/tokenomics.{json,md} and evidence/impact/impact.{json,md}.

    .venv/bin/python -m tests.eval.analyze --chosen optimized
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "evidence"


def load(name):
    p = EV / "eval" / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def run_stats(data):
    s, rs = data["summary"], data["results"]
    agents = {}
    for agent in ("intake", "scheduling"):
        runs = [r for c in rs for r in c["runs"] if r["agent"] == agent]
        if runs:
            agents[agent] = {
                "runs": len(runs),
                "mean_model_requests": round(statistics.mean(r["model_requests"] or 0 for r in runs), 2),
                "mean_tool_calls": round(statistics.mean(r["tool_calls"] or 0 for r in runs), 2),
                "mean_input_tokens": round(statistics.mean(r["input_tokens"] or 0 for r in runs)),
                "mean_cached_input_tokens": round(statistics.mean(r["cached_input_tokens"] or 0 for r in runs)),
                "mean_output_tokens": round(statistics.mean(r["output_tokens"] or 0 for r in runs)),
                "mean_latency_s": round(statistics.mean((r["latency_ms"] or 0) / 1000 for r in runs), 2),
                "mean_cost_usd": round(statistics.mean(r["cost_usd"] or 0 for r in runs), 6),
            }
    t = s["tokens"]
    sched = [c["usage"]["cost_usd"] for c in rs if c["status"] == "pending_review"]
    ninfo = [c["usage"]["cost_usd"] for c in rs if c["status"] == "needs_info"]
    return {
        "label": s["label"], "profile": s.get("profile"), "cases": s["cases"], "cases_passed": s["cases_passed"],
        "field_accuracy": s["field_accuracy_overall"], "schedule_correct": s["schedule_correct"],
        "input_tokens": t["input_tokens"], "cached_input_tokens": t["cached_input_tokens"],
        "cached_share_of_input": round(t["cached_input_tokens"] / t["input_tokens"], 3) if t["input_tokens"] else 0,
        "cache_write_tokens": t["cache_write_tokens"], "output_tokens": t["output_tokens"],
        "model_requests": t["model_requests"], "tool_calls": t["tool_calls"],
        "portkey_cache_hits": t.get("portkey_cache_hits", "n/a"),
        "cost_total_usd": s["cost_usd_total"], "cost_mean_per_request_usd": s["cost_usd_per_request_mean"],
        "cost_mean_scheduled_request_usd": round(statistics.mean(sched), 6) if sched else None,
        "cost_p90_scheduled_request_usd": round(sorted(sched)[int(0.9 * (len(sched) - 1))], 6) if sched else None,
        "cost_mean_needs_info_request_usd": round(statistics.mean(ninfo), 6) if ninfo else None,
        "latency_s": s["latency_seconds"], "per_agent": agents,
    }


def projections(st, clarify_share=0.25):
    """Expected cost per member request: scheduled requests cost C_s; a share needs one
    clarification round first (intake-only C_n) and then a full run (C_s)."""
    cs, cn = st["cost_mean_scheduled_request_usd"], st["cost_mean_needs_info_request_usd"] or 0
    per = (1 - clarify_share) * cs + clarify_share * (cn + cs)
    p90 = st["cost_p90_scheduled_request_usd"]
    per_hi = (1 - clarify_share) * p90 + clarify_share * (cn + p90)
    return {"assumptions": {"clarification_share": clarify_share,
                            "cost_scheduled_request_usd (measured mean)": cs,
                            "cost_needs_info_round_usd (measured mean)": cn,
                            "pricing": "OpenAI list price for gpt-6-luna (verified on developers.openai.com/api/docs/pricing); "
                                       "calls are routed to Azure OpenAI by the course Portkey config, whose billed rate we cannot see",
                            "excludes": "hosting, Portkey fees, staff time"},
            "expected_cost_per_member_request_usd": round(per, 6),
            "expected_cost_per_member_request_usd_p90": round(per_hi, 6),
            "table": {n: {"expected_usd": round(per * n, 4), "p90_usd": round(per_hi * n, 4),
                          "model_runs_approx": round(n * (2 + clarify_share * 1))} for n in (100, 1000, 10000)}}


def manual_estimate(data):
    """ESTIMATE (not observed): manual staff effort for the same requests, derived from the
    lookups the agents actually performed. Assumptions are explicit and adjustable."""
    per_lookup_min, fixed_min = (1.0, 2.0, 3.0), 4.0  # low/mid/high minutes per lookup; read + reply
    rows = []
    for c in data["results"]:
        lookups = sum(1 for t in c["tool_sequence"] if not t.endswith(("list_services", "get_member_profile")))
        rows.append(lookups)
    mean_l = statistics.mean(rows)
    return {"label": "ESTIMATE — not measured with real staff",
            "basis": "Each data lookup the agents performed (priest qualifications, languages, calendars, travel, "
                     "policies, slot checks) is treated as one manual lookup a staff member would do; plus "
                     f"{fixed_min} min to read the request and write a reply.",
            "mean_lookups_per_request (measured from agent traces)": round(mean_l, 2),
            "estimated_staff_minutes_per_request": {k: round(fixed_min + mean_l * v, 1)
                                                    for k, v in zip(("low", "mid", "high"), per_lookup_min)},
            "with_serve_staff_steps": "Open request, read evidence, click Approve (1 click) — or Edit & approve (form + check + approve)."}


def main(chosen: str):
    base, std, opt = load("baseline_phase1"), load("v2_standard"), load("v2_optimized")
    held = load(f"heldout_{chosen}")
    rules_main, rules_held = load("rules_only_baseline"), load("rules_only_heldout")
    tok_dir, imp_dir = EV / "tokenomics", EV / "impact"
    tok_dir.mkdir(parents=True, exist_ok=True)
    imp_dir.mkdir(parents=True, exist_ok=True)
    configs = {k: run_stats(v) for k, v in (("baseline_phase1", base), ("v2_standard", std), ("v2_optimized", opt)) if v}
    # Repeat runs (same cases, same code) to show run-to-run variance; projections use pooled results.
    repeats, pooled = {}, {}
    for prof in ("standard", "optimized"):
        runs = [x for x in (load(f"v2_{prof}"), load(f"v2_{prof}_r2")) if x]
        repeats[prof] = [{"label": r["summary"]["label"], "cases_passed": r["summary"]["cases_passed"],
                          "field_accuracy": r["summary"]["field_accuracy_overall"],
                          "schedule_correct": r["summary"]["schedule_correct"],
                          "cost_total_usd": r["summary"]["cost_usd_total"],
                          "latency_mean_s": r["summary"]["latency_seconds"]["mean"],
                          "failed_cases": r["summary"]["failed_cases"]} for r in runs]
        merged = {"summary": {**runs[0]["summary"]}, "results": [c for r in runs for c in r["results"]]}
        rs = merged["results"]
        merged["summary"]["cost_usd_total"] = round(sum(c["usage"]["cost_usd"] for c in rs), 6)
        merged["summary"]["cost_usd_per_request_mean"] = round(statistics.mean(c["usage"]["cost_usd"] for c in rs), 6)
        pooled[prof] = run_stats(merged)
    chosen_stats = configs[f"v2_{chosen}"]
    tok = {"configs": configs, "chosen_profile": chosen, "repeat_runs": repeats,
           "projection": projections(pooled[chosen]),
           "projection_other_profile": projections(pooled["standard" if chosen == "optimized" else "optimized"])}
    (tok_dir / "tokenomics.json").write_text(json.dumps(tok, indent=2))

    def row(c):
        return (f"| {c['label']} | {c['cases_passed']}/{c['cases']} | {c['field_accuracy']:.1%} | {c['schedule_correct']}/{c['cases']} | "
                f"{c['model_requests']} | {c['tool_calls']} | {c['input_tokens']:,} | {c['cached_input_tokens']:,} ({c['cached_share_of_input']:.0%}) | "
                f"{c['output_tokens']:,} | ${c['cost_total_usd']:.4f} | ${c['cost_mean_per_request_usd']:.5f} | {c['latency_s']['mean']}s / {c['latency_s']['p90']}s | {c['portkey_cache_hits']} |")
    md = ["# Tokenomics — measured on the same 27 evaluation cases", "",
          "All numbers are the API's own usage fields from real gpt-6-luna calls (Portkey cache bypassed; Portkey cache hits column must be 0). "
          "Cost = list price: $0.10/1M input, $0.01/1M cached input, $0.125/1M cache write, $0.50/1M output.", "",
          "| Config | Passed | Field acc. | Schedule ok | Model req. | Tool calls | Input tok | Cached input | Output tok | Total cost | Cost/request | Latency mean / p90 | Portkey cache hits |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"] + [row(c) for c in configs.values()]
    md += ["", "## Per agent (means per run)", "", "| Config | Agent | Model req. | Tool calls | Input | Cached | Output | Latency | Cost |", "|---|---|---|---|---|---|---|---|---|"]
    for c in configs.values():
        for a, v in c["per_agent"].items():
            md.append(f"| {c['label']} | {a} | {v['mean_model_requests']} | {v['mean_tool_calls']} | {v['mean_input_tokens']:,} | {v['mean_cached_input_tokens']:,} | {v['mean_output_tokens']:,} | {v['mean_latency_s']}s | ${v['mean_cost_usd']:.6f} |")
    md += ["", "## Run-to-run variance (same 27 cases, same code, separate runs)", "",
           "| Profile | Run | Passed | Field acc. | Schedule ok | Total cost | Mean latency | Failed cases |", "|---|---|---|---|---|---|---|---|"]
    for prof, rows in repeats.items():
        for r in rows:
            md.append(f"| {prof} | {r['label']} | {r['cases_passed']}/27 | {r['field_accuracy']:.1%} | {r['schedule_correct']}/27 | "
                      f"${r['cost_total_usd']:.4f} | {r['latency_mean_s']}s | {', '.join(r['failed_cases']) or '—'} |")
    p = tok["projection"]
    md += ["", f"## Projection (chosen profile: {chosen})", "",
           f"Expected cost per member request: **${p['expected_cost_per_member_request_usd']:.5f}** (p90 ${p['expected_cost_per_member_request_usd_p90']:.5f}), from both runs pooled. "
           f"Other profile for comparison: ${tok['projection_other_profile']['expected_cost_per_member_request_usd']:.5f}.", "",
           "| Member requests | Expected cost | p90 cost | ≈ agent runs |", "|---|---|---|---|"]
    for n, v in p["table"].items():
        md.append(f"| {int(n):,} | ${v['expected_usd']:.2f} | ${v['p90_usd']:.2f} | {v['model_runs_approx']:,} |")
    md += ["", "Assumptions: " + "; ".join(f"{k}: {v}" for k, v in p["assumptions"].items())]
    (tok_dir / "tokenomics.md").write_text("\n".join(md) + "\n")

    impact = {
        "ai_workflow_measured": {
            "main_set": {"profile": chosen, "cases_passed": chosen_stats["cases_passed"], "cases": chosen_stats["cases"],
                         "field_accuracy": chosen_stats["field_accuracy"], "schedule_correct": chosen_stats["schedule_correct"],
                         "seconds_to_recommendation_mean": chosen_stats["latency_s"]["mean"],
                         "seconds_to_recommendation_p90": chosen_stats["latency_s"]["p90"],
                         "cost_per_request_usd": chosen_stats["cost_mean_per_request_usd"]},
            "heldout_set": held["summary"] if held else None,
        },
        "phase1_agents_measured": {"cases_passed": configs["baseline_phase1"]["cases_passed"],
                                   "field_accuracy": configs["baseline_phase1"]["field_accuracy"]},
        "rules_only_measured": {"main_set": rules_main["summary"] if rules_main else None,
                                "heldout_set": rules_held["summary"] if rules_held else None,
                                "caveat": "Parser written by the test author; main-set score is not meaningful (written after seeing the cases). "
                                          "Held-out set was written after the parser was frozen."},
        "manual_estimate": manual_estimate(std),  # standard traces list every lookup explicitly
        "stakeholder_feedback": {"status": "NOT COLLECTED", "useful_to_collect": [
            "Temple office staff: how long a griha pravesh / satyanarayan request takes today (timed, 5-10 real requests)",
            "Priests: whether suggested slots respect real preparation/travel realities",
            "Members: whether the clarifying questions and proposed times are clear (5-question survey)",
            "Board/treasurer: acceptable cost per request and data-privacy expectations"]},
    }
    (imp_dir / "impact.json").write_text(json.dumps(impact, indent=2, default=str))
    m = impact["manual_estimate"]
    rh = rules_held["summary"] if rules_held else {}
    hs = held["summary"] if held else {}
    lines = ["# Operational impact", "", "## Measured (same scoring for every system)", "",
             "| System | Main set (27) passed | Main field acc. | Held-out (15) passed | Held-out field acc. | Time per request | Cost per request |",
             "|---|---|---|---|---|---|---|",
             f"| Phase 1 agents | {configs['baseline_phase1']['cases_passed']}/27 | {configs['baseline_phase1']['field_accuracy']:.1%} | not run (code superseded) | — | {configs['baseline_phase1']['latency_s']['mean']}s | ${configs['baseline_phase1']['cost_mean_per_request_usd']:.5f} |",
             f"| SERVE v2 agents ({chosen}) | {chosen_stats['cases_passed']}/27 | {chosen_stats['field_accuracy']:.1%} | {hs.get('cases_passed', '—')}/{hs.get('cases', '—')} | {hs.get('field_accuracy_overall', 0):.1%} | {chosen_stats['latency_s']['mean']}s | ${chosen_stats['cost_mean_per_request_usd']:.5f} |",
             f"| Rules-only keyword parser | {rules_main['summary']['cases_passed']}/27 (not meaningful*) | {rules_main['summary']['field_accuracy_overall']:.1%}* | {rh.get('cases_passed', '—')}/{rh.get('cases', '—')} | {rh.get('field_accuracy_overall', 0):.1%} | {rules_main['summary']['mean_ms']} ms | $0 |",
             "", "\\* written by the test author after seeing the main-set texts; the held-out set is the fair comparison.", "",
             "## Estimated (not measured with real staff)", "",
             f"- {m['basis']}",
             f"- Mean lookups per request (measured from agent traces): {m['mean_lookups_per_request (measured from agent traces)']}",
             f"- Estimated manual staff minutes per request: low {m['estimated_staff_minutes_per_request']['low']}, mid {m['estimated_staff_minutes_per_request']['mid']}, high {m['estimated_staff_minutes_per_request']['high']}",
             f"- With SERVE: {m['with_serve_staff_steps']}", "",
             "## Stakeholder feedback", "", "Not collected. Useful next steps:"] + [f"- {x}" for x in impact["stakeholder_feedback"]["useful_to_collect"]]
    (imp_dir / "impact.md").write_text("\n".join(lines) + "\n")
    print((tok_dir / "tokenomics.md").read_text())
    print((imp_dir / "impact.md").read_text())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--chosen", default="optimized", choices=["standard", "optimized"])
    main(ap.parse_args().chosen)
