# Evaluation: v2_standard

- Run at: 2026-10-25T21:19:26  ·  model requested: `gpt-6-luna`  ·  profile: `standard`
- Cases passed (all fields + scheduling correct): **27/27**
- Field accuracy overall: **100.0%**  ·  scheduling correct: **27/27**
- Agent proposals rejected by rules engine: 0  ·  bookings created by agents: 0  ·  pipeline errors: 0
- Latency per request (s): mean 15.25, median 16.19, p90 19.7, max 38.98
- Tokens: input 251,171 (cached 163,531, cache-write 69,496), output 20,630; model requests 144, tool calls 159
- Cost (list price): total $0.022452, mean per request $0.000832

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
| ✅ C01_griha_telugu_hamden | pending_review | 9/9 | ok | 2 | $0.00114 | 15.54 |  |
| ✅ C02_satya_late_morning_hindi | pending_review | 7/7 | ok | 3 | $0.00110 | 17.36 |  |
| ✅ C03_naming_gujarati_unqualified | pending_review | 6/6 | ok | 0 | $0.00059 | 9.42 |  |
| ✅ C04_archana_exact_evening | pending_review | 5/5 | ok | 3 | $0.00097 | 16.61 |  |
| ✅ C05_abhishekam_evening | pending_review | 5/5 | ok | 2 | $0.00090 | 14.11 |  |
| ✅ C06_consult_tamil_afternoon | pending_review | 6/6 | ok | 2 | $0.00092 | 15.05 |  |
| ✅ C07_missing_everything | needs_info | 2/2 | ok | 0 | $0.00029 | 5.47 |  |
| ✅ C08_missing_date | needs_info | 5/5 | ok | 0 | $0.00018 | 5.06 |  |
| ✅ C09_missing_location | needs_info | 5/5 | ok | 0 | $0.00021 | 5.38 |  |
| ✅ C10_home_city_from_profile | pending_review | 6/6 | ok | 3 | $0.00118 | 38.98 |  |
| ✅ C11_travel_beyond_radius | pending_review | 6/6 | ok | 0 | $0.00073 | 19.09 |  |
| ✅ C12_travel_fee_waterbury | pending_review | 6/6 | ok | 3 | $0.00102 | 13.27 |  |
| ✅ C13_travel_priest_limit | pending_review | 7/7 | ok | 3 | $0.00115 | 16.56 |  |
| ✅ C14_time_off_telugu | pending_review | 6/6 | ok | 2 | $0.00118 | 21.86 |  |
| ✅ C15_diwali_conflict | pending_review | 5/5 | ok | 3 | $0.00123 | 18.67 |  |
| ✅ C16_seeded_booking_conflict | pending_review | 5/5 | ok | 1 | $0.00073 | 13.81 |  |
| ✅ C17_unavailable_service | needs_info | 2/2 | ok | 0 | $0.00024 | 4.81 |  |
| ✅ C18_contradictory_location | pending_review | 5/5 | ok | 3 | $0.00108 | 18.94 |  |
| ✅ C19_contradictory_dates | pending_review | 5/5 | ok | 3 | $0.00100 | 27.64 |  |
| ✅ C20_accessibility_naming | pending_review | 8/8 | ok | 3 | $0.00113 | 18.08 |  |
| ✅ C21_language_unavailable | pending_review | 5/5 | ok | 0 | $0.00049 | 8.9 |  |
| ✅ C22_past_date | needs_info | 3/3 | ok | 0 | $0.00020 | 3.53 |  |
| ✅ C23_short_notice_griha | pending_review | 6/6 | ok | 0 | $0.00097 | 12.92 |  |
| ✅ C24_ambiguous_time | pending_review | 5/5 | ok | 3 | $0.00106 | 18.41 |  |
| ✅ C25_time_range_tamil | pending_review | 7/7 | ok | 2 | $0.00092 | 16.19 |  |
| ✅ C26_afternoon_griha | pending_review | 6/6 | ok | 2 | $0.00090 | 19.7 |  |
| ✅ C27_archana_exact_morning | pending_review | 5/5 | ok | 2 | $0.00093 | 16.38 |  |
