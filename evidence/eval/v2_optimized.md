# Evaluation: v2_optimized

- Run at: 2026-10-25T21:17:18  ·  model requested: `gpt-6-luna`  ·  profile: `optimized`
- Cases passed (all fields + scheduling correct): **26/27**
- Field accuracy overall: **99.3%**  ·  scheduling correct: **27/27**
- Agent proposals rejected by rules engine: 0  ·  bookings created by agents: 0  ·  pipeline errors: 0
- Latency per request (s): mean 10.52, median 9.98, p90 15.42, max 29.14
- Tokens: input 143,641 (cached 91,507, cache-write 40,164), output 16,240; model requests 95, tool calls 79
- Cost (list price): total $0.015253, mean per request $0.000565

## Field accuracy

| Field | Correct | Total | Accuracy |
|---|---|---|---|
| attendees | 3 | 3 | 100% |
| city | 9 | 9 | 100% |
| dates | 23 | 23 | 100% |
| language | 10 | 10 | 100% |
| location_type | 23 | 23 | 100% |
| missing | 5 | 5 | 100% |
| service_id | 25 | 25 | 100% |
| special_requirements | 2 | 2 | 100% |
| status | 26 | 27 | 96% |
| time | 21 | 21 | 100% |

## Cases

| Case | Status | Fields | Schedule | Options | Cost | Seconds | Problems |
|---|---|---|---|---|---|---|---|
| ✅ C01_griha_telugu_hamden | pending_review | 9/9 | ok | 2 | $0.00087 | 12.26 |  |
| ✅ C02_satya_late_morning_hindi | pending_review | 7/7 | ok | 3 | $0.00064 | 9.5 |  |
| ✅ C03_naming_gujarati_unqualified | pending_review | 6/6 | ok | 0 | $0.00047 | 11.32 |  |
| ✅ C04_archana_exact_evening | pending_review | 5/5 | ok | 3 | $0.00054 | 15.88 |  |
| ✅ C05_abhishekam_evening | pending_review | 5/5 | ok | 2 | $0.00062 | 9.56 |  |
| ✅ C06_consult_tamil_afternoon | pending_review | 6/6 | ok | 2 | $0.00057 | 29.14 |  |
| ✅ C07_missing_everything | needs_info | 2/2 | ok | 0 | $0.00019 | 3.7 |  |
| ✅ C08_missing_date | needs_info | 5/5 | ok | 0 | $0.00013 | 2.59 |  |
| ✅ C09_missing_location | needs_info | 5/5 | ok | 0 | $0.00013 | 2.94 |  |
| ✅ C10_home_city_from_profile | pending_review | 6/6 | ok | 3 | $0.00077 | 17.74 |  |
| ✅ C11_travel_beyond_radius | pending_review | 6/6 | ok | 0 | $0.00054 | 9.44 |  |
| ✅ C12_travel_fee_waterbury | pending_review | 6/6 | ok | 3 | $0.00069 | 12.93 |  |
| ✅ C13_travel_priest_limit | pending_review | 7/7 | ok | 3 | $0.00082 | 15.42 |  |
| ✅ C14_time_off_telugu | pending_review | 6/6 | ok | 3 | $0.00079 | 11.19 |  |
| ✅ C15_diwali_conflict | pending_review | 5/5 | ok | 3 | $0.00085 | 12.77 |  |
| ✅ C16_seeded_booking_conflict | pending_review | 5/5 | ok | 1 | $0.00058 | 9.14 |  |
| ✅ C17_unavailable_service | needs_info | 2/2 | ok | 0 | $0.00020 | 3.93 |  |
| ❌ C18_contradictory_location | needs_info | 4/5 | ok | 0 | $0.00076 | 13.02 | wrong: status |
| ✅ C19_contradictory_dates | pending_review | 5/5 | ok | 3 | $0.00066 | 9.48 |  |
| ✅ C20_accessibility_naming | pending_review | 8/8 | ok | 3 | $0.00064 | 10.06 |  |
| ✅ C21_language_unavailable | pending_review | 5/5 | ok | 0 | $0.00042 | 5.52 |  |
| ✅ C22_past_date | needs_info | 3/3 | ok | 0 | $0.00018 | 2.88 |  |
| ✅ C23_short_notice_griha | pending_review | 6/6 | ok | 0 | $0.00066 | 12.8 |  |
| ✅ C24_ambiguous_time | pending_review | 5/5 | ok | 3 | $0.00065 | 9.21 |  |
| ✅ C25_time_range_tamil | pending_review | 7/7 | ok | 2 | $0.00069 | 9.55 |  |
| ✅ C26_afternoon_griha | pending_review | 6/6 | ok | 2 | $0.00063 | 9.98 |  |
| ✅ C27_archana_exact_morning | pending_review | 5/5 | ok | 2 | $0.00058 | 12.03 |  |
