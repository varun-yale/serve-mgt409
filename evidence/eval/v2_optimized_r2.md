# Evaluation: v2_optimized_r2

- Run at: 2026-10-25T21:28:25  ·  model requested: `gpt-6-luna`  ·  profile: `optimized`
- Cases passed (all fields + scheduling correct): **27/27**
- Field accuracy overall: **100.0%**  ·  scheduling correct: **27/27**
- Agent proposals rejected by rules engine: 0  ·  bookings created by agents: 0  ·  pipeline errors: 0
- Latency per request (s): mean 10.07, median 10.2, p90 14.85, max 22.65
- Tokens: input 145,446 (cached 116,728, cache-write 16,622), output 15,942; model requests 96, tool calls 79
- Cost (list price): total $0.012426, mean per request $0.000460

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
| status | 27 | 27 | 100% |
| time | 21 | 21 | 100% |

## Cases

| Case | Status | Fields | Schedule | Options | Cost | Seconds | Problems |
|---|---|---|---|---|---|---|---|
| ✅ C01_griha_telugu_hamden | pending_review | 9/9 | ok | 2 | $0.00055 | 11.9 |  |
| ✅ C02_satya_late_morning_hindi | pending_review | 7/7 | ok | 3 | $0.00058 | 11.67 |  |
| ✅ C03_naming_gujarati_unqualified | pending_review | 6/6 | ok | 0 | $0.00026 | 5.61 |  |
| ✅ C04_archana_exact_evening | pending_review | 5/5 | ok | 3 | $0.00034 | 6.99 |  |
| ✅ C05_abhishekam_evening | pending_review | 5/5 | ok | 2 | $0.00046 | 9.92 |  |
| ✅ C06_consult_tamil_afternoon | pending_review | 6/6 | ok | 2 | $0.00048 | 10.52 |  |
| ✅ C07_missing_everything | needs_info | 2/2 | ok | 0 | $0.00014 | 2.94 |  |
| ✅ C08_missing_date | needs_info | 5/5 | ok | 0 | $0.00011 | 2.77 |  |
| ✅ C09_missing_location | needs_info | 5/5 | ok | 0 | $0.00011 | 3.18 |  |
| ✅ C10_home_city_from_profile | pending_review | 6/6 | ok | 3 | $0.00067 | 16.72 |  |
| ✅ C11_travel_beyond_radius | pending_review | 6/6 | ok | 0 | $0.00047 | 9.26 |  |
| ✅ C12_travel_fee_waterbury | pending_review | 6/6 | ok | 3 | $0.00047 | 10.42 |  |
| ✅ C13_travel_priest_limit | pending_review | 7/7 | ok | 3 | $0.00070 | 10.71 |  |
| ✅ C14_time_off_telugu | pending_review | 6/6 | ok | 0 | $0.00064 | 13.9 |  |
| ✅ C15_diwali_conflict | pending_review | 5/5 | ok | 3 | $0.00066 | 17.98 |  |
| ✅ C16_seeded_booking_conflict | pending_review | 5/5 | ok | 1 | $0.00041 | 9.09 |  |
| ✅ C17_unavailable_service | needs_info | 2/2 | ok | 0 | $0.00019 | 4.69 |  |
| ✅ C18_contradictory_location | pending_review | 5/5 | ok | 3 | $0.00088 | 14.73 |  |
| ✅ C19_contradictory_dates | pending_review | 5/5 | ok | 3 | $0.00048 | 9.26 |  |
| ✅ C20_accessibility_naming | pending_review | 8/8 | ok | 3 | $0.00066 | 10.27 |  |
| ✅ C21_language_unavailable | pending_review | 5/5 | ok | 0 | $0.00029 | 5.99 |  |
| ✅ C22_past_date | needs_info | 3/3 | ok | 0 | $0.00010 | 2.33 |  |
| ✅ C23_short_notice_griha | pending_review | 6/6 | ok | 0 | $0.00054 | 13.68 |  |
| ✅ C24_ambiguous_time | pending_review | 5/5 | ok | 3 | $0.00052 | 9.63 |  |
| ✅ C25_time_range_tamil | pending_review | 7/7 | ok | 2 | $0.00054 | 10.2 |  |
| ✅ C26_afternoon_griha | pending_review | 6/6 | ok | 2 | $0.00055 | 22.65 |  |
| ✅ C27_archana_exact_morning | pending_review | 5/5 | ok | 2 | $0.00062 | 14.85 |  |
