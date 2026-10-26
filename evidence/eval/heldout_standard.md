# Evaluation: heldout_standard

- Run at: 2026-10-25T21:23:31  ·  model requested: `gpt-6-luna`  ·  profile: `standard`
- Cases passed (all fields + scheduling correct): **14/15**
- Field accuracy overall: **97.5%**  ·  scheduling correct: **15/15**
- Agent proposals rejected by rules engine: 0  ·  bookings created by agents: 0  ·  pipeline errors: 0
- Latency per request (s): mean 14.17, median 15.8, p90 18.87, max 22.32
- Tokens: input 140,038 (cached 91,481, cache-write 38,603), output 11,673; model requests 79, tool calls 89
- Cost (list price): total $0.012572, mean per request $0.000838

## Field accuracy

| Field | Correct | Total | Accuracy |
|---|---|---|---|
| attendees | 1 | 1 | 100% |
| city | 5 | 6 | 83% |
| dates | 13 | 13 | 100% |
| language | 6 | 6 | 100% |
| location_type | 13 | 13 | 100% |
| missing | 2 | 2 | 100% |
| service_id | 13 | 13 | 100% |
| special_requirements | 1 | 1 | 100% |
| status | 14 | 15 | 93% |
| time | 11 | 11 | 100% |

## Cases

| Case | Status | Fields | Schedule | Options | Cost | Seconds | Problems |
|---|---|---|---|---|---|---|---|
| ✅ H01_gruhapravesam_casual | pending_review | 7/7 | ok | 2 | $0.00101 | 18.87 |  |
| ✅ H02_vratham_11ish | pending_review | 7/7 | ok | 3 | $0.00104 | 15.86 |  |
| ✅ H03_archanai_after_6 | pending_review | 5/5 | ok | 3 | $0.00110 | 15.25 |  |
| ✅ H04_namkaran_wheelchair | pending_review | 7/7 | ok | 3 | $0.00103 | 19.45 |  |
| ✅ H05_generic_pooja | needs_info | 2/2 | ok | 0 | $0.00020 | 4.71 |  |
| ✅ H06_terse_abhishek | pending_review | 5/5 | ok | 2 | $0.00092 | 16.38 |  |
| ✅ H07_named_priest_too_far | pending_review | 6/6 | ok | 2 | $0.00101 | 15.79 |  |
| ✅ H08_consult_after_4 | pending_review | 5/5 | ok | 3 | $0.00102 | 15.8 |  |
| ✅ H09_vehicle_puja | needs_info | 2/2 | ok | 0 | $0.00025 | 5.33 |  |
| ✅ H10_katha_after_lunch | pending_review | 7/7 | ok | 2 | $0.00101 | 14.33 |  |
| ✅ H11_named_priest_busy | pending_review | 5/5 | ok | 1 | $0.00076 | 16.22 |  |
| ✅ H12_beyond_radius | pending_review | 5/5 | ok | 0 | $0.00070 | 11.91 |  |
| ❌ H13_housewarming_tomorrow | needs_info | 3/5 | ok | 0 | $0.00017 | 4.52 | wrong: status, city |
| ✅ H14_price_claim | pending_review | 6/6 | ok | 2 | $0.00091 | 15.85 |  |
| ✅ H15_all_caps_terse | pending_review | 7/7 | ok | 3 | $0.00143 | 22.32 |  |
