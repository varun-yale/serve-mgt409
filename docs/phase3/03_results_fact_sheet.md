# Results fact sheet (copy numbers from here; every row points to its evidence file)

All model results: real `gpt-6-luna` calls via Portkey (Azure OpenAI deployment, reported as
`gpt-6-luna-global`), Portkey cache bypassed, **0 cache hits** in every run below. Fictional data.
Costs are **list-price estimates** (OpenAI pricing verified; Azure billed rate not visible).
Run date: 2026-10-25.

## A. Measured — accuracy (same scorer for every system)

| System | Main set (27) | Field accuracy | Scheduling correct | Held-out (15) | Held-out field acc. | Evidence |
|---|---|---|---|---|---|---|
| Phase 1 agents (baseline) | 21/27 | 95.9% (time field 71.4%) | 22/27 | not run | — | `evidence/eval/baseline_phase1.json` |
| v2 standard, run 1 / run 2 | 27/27 · 26/27 | 100% · 98.6% | 27 · 26 | 14/15 | 97.5% | `eval/v2_standard*.json`, `eval/heldout_standard.json` |
| **v2 optimized (default), run 1 / run 2** | **26/27 · 27/27** | **99.3% · 100%** | **27 · 27** | **14/15** | **98.8%** | `eval/v2_optimized*.json`, `eval/heldout_optimized.json` |
| Rules-only keyword parser | 27/27 *(invalid — written after seeing cases)* | — | — | **10/15** | 88.9% | `eval/rules_only_heldout.json` |

All six baseline failures were time-of-day handling (late morning, exact times, a time range).
Remaining v2 failures are conservative: asking instead of using the profile town (C10, H13),
confirming a contradictory location (C18), reading "after 4" as any time (H08).

Across all v2 runs: **0** pipeline errors · **0** bookings created by agents · **0** agent
proposals rejected by the rules engine.

## B. Measured — safety (`evidence/safety/safety_results_{optimized,standard}.md`)

| | Optimized | Standard |
|---|---|---|
| Attacks | 12 | 12 |
| Unsafe outcomes, new defenses OFF | 2 (duplicate processing; admin-token guessing) | 2 (same) |
| Unsafe outcomes, defenses ON | **0** | **0** |
| Already resisted by original design | 10 | 10 |
| Legitimate controls working, defenses ON | 2/2 (no false-positive flags) | 2/2 |
| Attacks flagged for staff by injection screening (D2) | **5** (A01, A02, A03, A07, A12) | same 5 |

(Correction: the Phase 2 chat summary said "6"; the evidence files show 5. A02 carries two patterns, approval_bypass + delimiter_injection, but it is one attack.)

D5 tool budgets: not triggered by the real model; verified with a scripted model
(`tests/test_phase2.py`: 9th search refused; 100-step loop stopped by limits).
Deterministic test suite: **43/43** pass. Phase 1 end-to-end regression on v2 code: **17/17**.

## C. Measured — tokenomics and latency (`evidence/tokenomics/tokenomics.md`)

| Config (27 cases, run 1) | Model requests | Tool calls | Input tokens | Cached input | Output | Cost / request | Mean / p90 latency |
|---|---|---|---|---|---|---|---|
| Phase 1 | 139 | 160 | 210,093 | 97,013 (46%) | 20,229 | $0.00088 | 13.6 s / 19.4 s |
| v2 standard | 144 | 159 | 251,171 | 163,531 (65%) | 20,630 | $0.00083 | 15.3 s / 19.7 s |
| **v2 optimized** | **95** | **79** | **143,641** | **91,507 (64%)** | **16,240** | **$0.00056** | **10.5 s / 15.4 s** |

Optimized vs standard (run 1): −34% model requests, −50% tool calls, −43% input tokens,
−32% cost per request, −31% mean latency; same safety outcome; accuracy within run-to-run noise.
Run 2 optimized: $0.00046/request, 10.1 s mean. Caching verified from API usage fields
(`cached_tokens`), not assumed.

## D. Projections (assumption-based — label as projections)

| Member requests | Expected cost | p90 | Assumptions |
|---|---|---|---|
| 100 | $0.06 | $0.08 | Optimized profile, both runs pooled: $0.000592 per scheduled request, $0.000202 per clarification round, 25% of requests need one clarification → **$0.00064 per member request** (p90 $0.00082). List price; excludes hosting, Portkey fees and staff time. |
| 1,000 | $0.64 | $0.82 | |
| 10,000 | $6.42 | $8.24 | |

## E. Measured — workload behind a request (`evidence/impact/manual_workload.md`)
35 complete requests: mean 3.5 qualified priests, 2.5 after language, 2.5 calendars, 30.8
candidate slots, 276.9 rule checks; 15/35 need a travel lookup; 9/35 correctly end in "no
availability". SERVE: ~10.5 s and one approval click.

## F. Estimates (not measured — always label)
- Manual staff time per request: **≈ 9–18 min** (from agent-trace lookups × 1–3 min + 4 min
  read/reply; `evidence/impact/impact.md`) or **≈ 15.5 min** (corrected in Phase 4 from an earlier mistyped 14.3; from the deterministic workload
  model: 1 min/calendar + 0.25 min/candidate slot + 3 min travel + 4 min; `manual_workload.md`).
  No real staff were timed.
- Stakeholder feedback: **none collected.**

## G. Other verified facts
- Fresh-copy cold start (`start.sh` on a copy without dependencies, build or DB): serving in
  14 s on this machine with warm pip/npm caches; handled a real AI request end to end. A grader's
  first install will take longer (not measured).
- Model routing: requesting `gpt-6-luna-global` directly returned `gpt-5.6-luna-global` → model
  guard added; any non-`gpt-6-luna*` response fails the run.
- Portkey cache: an early baseline rerun was 100% cache replays → quarantined as INVALID; cache
  bypass now default.

## Claims register (use only claims marked OK)

| Claim | Status |
|---|---|
| "Agents correctly handle 26–27 of 27 evaluation cases and 14 of 15 held-out cases" | OK — measured |
| "Accuracy improved from 21/27 to 26–27/27 after fixing time handling" | OK — measured |
| "AI beats a rules-only parser on messy phrasing (14/15 vs 10/15)" | OK — held-out; small sample, author-written cases |
| "No agent can create a booking; 0 unsafe outcomes in 12 attacks with defenses on" | OK — measured; state 10 were already resisted |
| "Costs about $0.0005–0.0006 per request" | OK — list-price estimate |
| "≈ $0.64 per 1,000 requests" | OK only as a projection with assumptions |
| "Saves staff ~10–15 minutes per request" | **Estimate only** — must be labelled |
| "Temples report…" / "users love…" / adoption numbers | **Not allowed** — no data |
| "First AI temple-management platform" | **Not allowed** — research-limited; say "we found no product that…" |
| "SERVE handles donations, volunteering and events" | **Not allowed as AI/production claim** — demo UI only; roadmap |
