# Tokenomics — measured on the same 27 evaluation cases

All numbers are the API's own usage fields from real gpt-6-luna calls (Portkey cache bypassed; Portkey cache hits column must be 0). Cost = list price: $0.10/1M input, $0.01/1M cached input, $0.125/1M cache write, $0.50/1M output.

| Config | Passed | Field acc. | Schedule ok | Model req. | Tool calls | Input tok | Cached input | Output tok | Total cost | Cost/request | Latency mean / p90 | Portkey cache hits |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline_phase1 | 21/27 | 95.9% | 22/27 | 139 | 160 | 210,093 | 97,013 (46%) | 20,229 | $0.0238 | $0.00088 | 13.6s / 19.41s | 0 |
| v2_standard | 27/27 | 100.0% | 27/27 | 144 | 159 | 251,171 | 163,531 (65%) | 20,630 | $0.0225 | $0.00083 | 15.25s / 19.7s | 0 |
| v2_optimized | 26/27 | 99.3% | 27/27 | 95 | 79 | 143,641 | 91,507 (64%) | 16,240 | $0.0153 | $0.00056 | 10.52s / 15.42s | 0 |

## Per agent (means per run)

| Config | Agent | Model req. | Tool calls | Input | Cached | Output | Latency | Cost |
|---|---|---|---|---|---|---|---|---|
| baseline_phase1 | intake | 2.07 | 1.07 | 2,280 | 1,142 | 201 | 5.17s | $0.000228 |
| baseline_phase1 | scheduling | 3.77 | 5.95 | 6,751 | 3,008 | 672 | 10.31s | $0.000800 |
| v2_standard | intake | 2.07 | 1.07 | 3,065 | 2,346 | 197 | 5.08s | $0.000205 |
| v2_standard | scheduling | 4 | 5.91 | 7,655 | 4,554 | 696 | 12.45s | $0.000768 |
| v2_optimized | intake | 1.07 | 0.07 | 1,595 | 1,358 | 196 | 2.91s | $0.000138 |
| v2_optimized | scheduling | 3 | 3.5 | 4,572 | 2,493 | 498 | 9.3s | $0.000524 |

## Run-to-run variance (same 27 cases, same code, separate runs)

| Profile | Run | Passed | Field acc. | Schedule ok | Total cost | Mean latency | Failed cases |
|---|---|---|---|---|---|---|---|
| standard | v2_standard | 27/27 | 100.0% | 27/27 | $0.0225 | 15.25s | — |
| standard | v2_standard_r2 | 26/27 | 98.6% | 26/27 | $0.0177 | 14.21s | C10_home_city_from_profile |
| optimized | v2_optimized | 26/27 | 99.3% | 27/27 | $0.0153 | 10.52s | C18_contradictory_location |
| optimized | v2_optimized_r2 | 27/27 | 100.0% | 27/27 | $0.0124 | 10.07s | — |

## Projection (chosen profile: optimized)

Expected cost per member request: **$0.00064** (p90 $0.00082), from both runs pooled. Other profile for comparison: $0.00093.

| Member requests | Expected cost | p90 cost | ≈ agent runs |
|---|---|---|---|
| 100 | $0.06 | $0.08 | 225 |
| 1,000 | $0.64 | $0.82 | 2,250 |
| 10,000 | $6.42 | $8.23 | 22,500 |

Assumptions: clarification_share: 0.25; cost_scheduled_request_usd (measured mean): 0.000592; cost_needs_info_round_usd (measured mean): 0.000202; pricing: OpenAI list price for gpt-6-luna (verified on developers.openai.com/api/docs/pricing); calls are routed to Azure OpenAI by the course Portkey config, whose billed rate we cannot see; excludes: hosting, Portkey fees, staff time
