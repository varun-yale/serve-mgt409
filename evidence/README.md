# SERVE evidence index

All model results come from real `gpt-6-luna` calls through the course Portkey config, with
Portkey's response cache bypassed (every run records `portkey_cache` = REFRESH; cache hits = 0).
All people, priests and bookings are fictional demonstration data. No credentials appear in
these files (scanned for the Portkey key and admin tokens).

| What | Files |
|---|---|
| One-page summary (rendered tables) | `evidence_summary.html` |
| Architecture + agent–tool workflow diagrams | `architecture.md` |
| **Evaluation set** (27 cases + expected outputs) | `../tests/eval/cases.py` |
| **Held-out set** (15 messier cases, written after the rules parser was frozen) | `../tests/eval/heldout_cases.py`, `eval/rules_baseline_frozen_sha256.txt` |
| Phase 1 baseline (real) | `eval/baseline_phase1.{json,md,log}`, code: `eval/phase1_code_snapshot/` |
| v2 standard / optimized, two runs each | `eval/v2_standard*.{json,md,log}`, `eval/v2_optimized*.{json,md,log}` |
| Held-out runs | `eval/heldout_standard.*`, `eval/heldout_optimized.*` |
| Rules-only baseline | `eval/rules_only_baseline.json` (not meaningful — see caveat), `eval/rules_only_heldout.json` |
| Invalid run kept for transparency | `eval/INVALID_portkey_cache_replay_baseline_phase1.*` (Portkey cache replay), `eval/baseline_phase1_attempt1_console.txt`, `eval/cache_probe/` |
| Safety suite (defenses off vs on) | `safety/safety_results_{optimized,standard}.{json,md}`, crashed harness attempts kept as `safety/attempt*_console.txt` |
| Tokenomics + projections | `tokenomics/tokenomics.{json,md}` |
| Operational impact (measured + clearly labelled estimates) | `impact/impact.{json,md}`, `impact/manual_workload.{json,md}` (deterministic workload per request) |
| Phase 1 end-to-end evidence + DB snapshot | `phase1/` |
| Phase 1 regression on v2 code (17/17) | `phase2_regression/` (first attempt with an outdated check: `phase2_regression_attempt1/`) |
| Phase 2 screenshots | `phase2_screenshots/` |
