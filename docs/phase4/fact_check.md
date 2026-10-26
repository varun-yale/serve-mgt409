# Phase 4 fact check — every number in report.html / slides.html

All values below are read at build time by `docs/phase4/build_deliverables.py` from the listed
files (no hand-typed metrics), except the items marked **constant**, which were checked by hand.

| Claim in deliverables | Value | Source (file → field) |
|---|---|---|
| Phase 1 cases passed | 21/27; time-field accuracy 71.4% | `evidence/eval/baseline_phase1.json` → summary.cases_passed, field_accuracy_by_field.time |
| v2 standard runs | 27/27, 26/27 | `eval/v2_standard.json`, `eval/v2_standard_r2.json` → cases_passed |
| v2 optimized runs | 26/27, 27/27 | `eval/v2_optimized.json`, `eval/v2_optimized_r2.json` |
| Held-out agents | 14/15 (optimized 98.8% fields; standard 97.5%) | `eval/heldout_{optimized,standard}.json` |
| Held-out rules-only | 10/15 (88.9% fields) | `eval/rules_only_heldout.json` |
| Cost per request standard / optimized (run 1) | $0.00083 / $0.00056 | `tokenomics/tokenomics.json` → configs.*.cost_mean_per_request_usd |
| Mean latency standard / optimized | 15.3 s / 10.5 s (p90 19.7 / 15.4) | same → latency_s |
| Model requests, tool calls, tokens, cached share, cache writes | 144/159/251,171/65%/69,496 vs 95/79/143,641/64%/40,164 | same → configs |
| Per-agent means (intake 2.07→1.07 requests, etc.) | — | same → per_agent |
| Percent changes (−34% requests, −50% tool calls, −43% input, −32% cost, −31% latency) | computed | from the two configs above |
| Projection per member request | $0.00064 (p90 $0.00082) | `tokenomics.json` → projection |
| 100 / 1,000 / 10,000 requests | $0.06 / $0.64 / $6.42 (p90 $0.08 / $0.82 / $8.24) | same → projection.table |
| Per-month scenarios | 100 / 500 / 2,000 requests × $0.00064 | **assumptions** (labelled illustrative) × projection |
| Safety | 12 attacks; 2 unsafe off; 0 on; 10 by design; 5 flagged; 2/2 controls | `safety/safety_results_optimized.json` (standard identical: `safety_results_standard.json`) |
| Workload | 3.5 priests, 2.5 language-ok, 2.5 calendars, 30.8 slots, ≈277 rule checks, 15/35 travel, 9/35 no availability | `impact/manual_workload.json` → summary |
| Manual estimates | 9–18 min (trace-based); ≈15.5 min (workload-based) | `impact/impact.json` → manual_estimate; `manual_workload.json` → minutes_estimate |
| End-to-end run facts (R1 extraction, 2 options, booking bk_991c13454e, 409s, run tokens/cost) | — | `evidence/phase2_regression/e2e_results.json` |
| Deterministic tests | 43 | collected by pytest at build time |
| Regression checks | 17/17 | `phase2_regression/e2e_results.json` → passed/total |
| Pricing | $0.10 / $0.01 / $0.125 / $0.50 per 1M | `backend/prices.json` (verified on developers.openai.com/api/docs/pricing) |
| Portkey replay ≈7× faster | 13.6 s vs 1.89 s mean = 7.2× | `eval/baseline_phase1.json` vs `eval/INVALID_portkey_cache_replay_baseline_phase1.json` |
| Rules parser ≈1 ms | 1.3 ms mean | `eval/rules_only_baseline.json` → mean_ms |
| Agent limits (4/4, 10/16, 120 s), D4 5 per 10 min, D6 10 fails / 5 min, late morning 10:00–11:59 | **constant** | `backend/agents.py`, `defenses.py`, `scheduling.py` |
| Population / temple counts | 3.0M (2020), +55%, ≈1%, ~1,600 (c. 2011) | Pew, Pew RLS, ARDA — `docs/phase3/05_sources.md` |
| Temple Hub $499/month | **constant** | third-party listings (SourceForge/GoodFirms), labelled “listed” |

## Discrepancies found while building
- Phase 3 docs said the workload-based manual estimate was ≈14.3 min; the evidence file says
  **15.5 min**. The deliverables use 15.5; Phase 3 docs corrected with a note.
- Phase 2 chat summary said 6 attacks were flagged; evidence shows **5** (already corrected in Phase 3).
- Phase 1 latency numbers (partly Portkey cache replays) are **not** used anywhere.

## Screenshots used (all real application, fictional data)
`docs/phase4/assets/*.jpg` are crops/resizes (macOS `sips`) of: `evidence/phase2_regression/screenshots/`
(landing, member request, member status, admin detail, member profile), `evidence/phase2_screenshots/`
(injection flagged, late-morning window), and `evidence/phase4_screenshots/` (agent trace, booking
confirmed, conflict blocked — captured in Phase 4 from the running app without model calls).
