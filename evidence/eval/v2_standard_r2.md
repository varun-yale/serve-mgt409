# Evaluation: v2_standard_r2

- Run at: 2026-10-25T21:30:17  ·  model requested: `gpt-6-luna`  ·  profile: `standard`
- Cases passed (all fields + scheduling correct): **26/27**
- Field accuracy overall: **98.6%**  ·  scheduling correct: **26/27**
- Agent proposals rejected by rules engine: 0  ·  bookings created by agents: 0  ·  pipeline errors: 0
- Latency per request (s): mean 14.21, median 14.77, p90 19.04, max 29.56
- Tokens: input 237,480 (cached 184,992, cache-write 35,478), output 19,495; model requests 135, tool calls 153
- Cost (list price): total $0.017733, mean per request $0.000657

## Field accuracy

| Field | Correct | Total | Accuracy |
|---|---|---|---|
| attendees | 3 | 3 | 100% |
| city | 8 | 9 | 89% |
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
| ✅ C01_griha_telugu_hamden | pending_review | 9/9 | ok | 2 | $0.00081 | 15.59 |  |
| ✅ C02_satya_late_morning_hindi | pending_review | 7/7 | ok | 3 | $0.00087 | 29.56 |  |
| ✅ C03_naming_gujarati_unqualified | pending_review | 6/6 | ok | 0 | $0.00033 | 10.24 |  |
| ✅ C04_archana_exact_evening | pending_review | 5/5 | ok | 3 | $0.00095 | 15.46 |  |
| ✅ C05_abhishekam_evening | pending_review | 5/5 | ok | 2 | $0.00071 | 14.32 |  |
| ✅ C06_consult_tamil_afternoon | pending_review | 6/6 | ok | 2 | $0.00064 | 11.27 |  |
| ✅ C07_missing_everything | needs_info | 2/2 | ok | 0 | $0.00026 | 9.9 |  |
| ✅ C08_missing_date | needs_info | 5/5 | ok | 0 | $0.00015 | 4.02 |  |
| ✅ C09_missing_location | needs_info | 5/5 | ok | 0 | $0.00014 | 4.41 |  |
| ❌ C10_home_city_from_profile | needs_info | 4/6 | fail | 0 | $0.00016 | 5.69 | wrong: status, city; expected at least one valid option, got none |
| ✅ C11_travel_beyond_radius | pending_review | 6/6 | ok | 0 | $0.00049 | 11.07 |  |
| ✅ C12_travel_fee_waterbury | pending_review | 6/6 | ok | 3 | $0.00080 | 13.52 |  |
| ✅ C13_travel_priest_limit | pending_review | 7/7 | ok | 3 | $0.00097 | 19.04 |  |
| ✅ C14_time_off_telugu | pending_review | 6/6 | ok | 3 | $0.00113 | 17.83 |  |
| ✅ C15_diwali_conflict | pending_review | 5/5 | ok | 3 | $0.00105 | 18.08 |  |
| ✅ C16_seeded_booking_conflict | pending_review | 5/5 | ok | 1 | $0.00057 | 14.77 |  |
| ✅ C17_unavailable_service | needs_info | 2/2 | ok | 0 | $0.00018 | 4.98 |  |
| ✅ C18_contradictory_location | pending_review | 5/5 | ok | 3 | $0.00112 | 18.39 |  |
| ✅ C19_contradictory_dates | pending_review | 5/5 | ok | 3 | $0.00072 | 15.09 |  |
| ✅ C20_accessibility_naming | pending_review | 8/8 | ok | 3 | $0.00110 | 15.04 |  |
| ✅ C21_language_unavailable | pending_review | 5/5 | ok | 0 | $0.00038 | 9.03 |  |
| ✅ C22_past_date | needs_info | 3/3 | ok | 0 | $0.00018 | 6.35 |  |
| ✅ C23_short_notice_griha | pending_review | 6/6 | ok | 0 | $0.00088 | 14.75 |  |
| ✅ C24_ambiguous_time | pending_review | 5/5 | ok | 3 | $0.00081 | 19.02 |  |
| ✅ C25_time_range_tamil | pending_review | 7/7 | ok | 2 | $0.00080 | 29.17 |  |
| ✅ C26_afternoon_griha | pending_review | 6/6 | ok | 2 | $0.00084 | 17.47 |  |
| ✅ C27_archana_exact_morning | pending_review | 5/5 | ok | 2 | $0.00070 | 19.71 |  |
