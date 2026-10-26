# Evaluation: heldout_optimized

- Run at: 2026-10-25T21:22:48  ·  model requested: `gpt-6-luna`  ·  profile: `optimized`
- Cases passed (all fields + scheduling correct): **14/15**
- Field accuracy overall: **98.8%**  ·  scheduling correct: **15/15**
- Agent proposals rejected by rules engine: 0  ·  bookings created by agents: 0  ·  pipeline errors: 0
- Latency per request (s): mean 11.34, median 11.38, p90 13.62, max 22.5
- Tokens: input 91,915 (cached 60,432, cache-write 23,923), output 10,058; model requests 60, tool calls 50
- Cost (list price): total $0.009380, mean per request $0.000625

## Field accuracy

| Field | Correct | Total | Accuracy |
|---|---|---|---|
| attendees | 1 | 1 | 100% |
| city | 6 | 6 | 100% |
| dates | 13 | 13 | 100% |
| language | 6 | 6 | 100% |
| location_type | 13 | 13 | 100% |
| missing | 2 | 2 | 100% |
| service_id | 13 | 13 | 100% |
| special_requirements | 1 | 1 | 100% |
| status | 15 | 15 | 100% |
| time | 10 | 11 | 91% |

## Cases

| Case | Status | Fields | Schedule | Options | Cost | Seconds | Problems |
|---|---|---|---|---|---|---|---|
| ✅ H01_gruhapravesam_casual | pending_review | 7/7 | ok | 2 | $0.00065 | 13.38 |  |
| ✅ H02_vratham_11ish | pending_review | 7/7 | ok | 3 | $0.00068 | 22.5 |  |
| ✅ H03_archanai_after_6 | pending_review | 5/5 | ok | 3 | $0.00084 | 14.91 |  |
| ✅ H04_namkaran_wheelchair | pending_review | 7/7 | ok | 3 | $0.00068 | 9.65 |  |
| ✅ H05_generic_pooja | needs_info | 2/2 | ok | 0 | $0.00013 | 2.69 |  |
| ✅ H06_terse_abhishek | pending_review | 5/5 | ok | 2 | $0.00061 | 10.68 |  |
| ✅ H07_named_priest_too_far | pending_review | 6/6 | ok | 2 | $0.00071 | 13.03 |  |
| ❌ H08_consult_after_4 | pending_review | 4/5 | ok | 3 | $0.00072 | 13.62 | wrong: time |
| ✅ H09_vehicle_puja | needs_info | 2/2 | ok | 0 | $0.00018 | 3.53 |  |
| ✅ H10_katha_after_lunch | pending_review | 7/7 | ok | 2 | $0.00068 | 10.17 |  |
| ✅ H11_named_priest_busy | pending_review | 5/5 | ok | 1 | $0.00057 | 11.38 |  |
| ✅ H12_beyond_radius | pending_review | 5/5 | ok | 0 | $0.00056 | 8.51 |  |
| ✅ H13_housewarming_tomorrow | pending_review | 5/5 | ok | 0 | $0.00089 | 12.78 |  |
| ✅ H14_price_claim | pending_review | 6/6 | ok | 2 | $0.00065 | 10.02 |  |
| ✅ H15_all_caps_terse | pending_review | 7/7 | ok | 0 | $0.00083 | 13.27 |  |
