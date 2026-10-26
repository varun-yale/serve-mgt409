# Evaluation: baseline_phase1

- Run at: 2026-10-25T21:03:29  ·  model requested: `gpt-6-luna`  ·  profile: `default`
- Cases passed (all fields + scheduling correct): **21/27**
- Field accuracy overall: **95.9%**  ·  scheduling correct: **23/27**
- Agent proposals rejected by rules engine: 0  ·  bookings created by agents: 0  ·  pipeline errors: 0
- Latency per request (s): mean 1.89, median 1.67, p90 2.73, max 4.28
- Tokens: input 208,820 (cached 62,600, cache-write 88,141), output 20,605; model requests 136, tool calls 164
- Cost (list price): total $0.027754, mean per request $0.001028

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
| time | 15 | 21 | 71% |

## Cases

| Case | Status | Fields | Schedule | Options | Cost | Seconds | Problems |
|---|---|---|---|---|---|---|---|
| ✅ C01_griha_telugu_hamden | pending_review | 9/9 | ok | 2 | $0.00116 | 4.28 |  |
| ❌ C02_satya_late_morning_hindi | pending_review | 6/7 | fail | 3 | $0.00113 | 1.71 | wrong: time; pr_dube 2026-11-01 07:00: outside window 10:00-11:59; pr_sharma 2026-11-01 07:00: outside window 10:00-11:59; pr_joshi 2026-11-01 08:00: outside window 10:00-11:59 |
| ✅ C03_naming_gujarati_unqualified | pending_review | 6/6 | ok | 0 | $0.00075 | 1.01 |  |
| ❌ C04_archana_exact_evening | pending_review | 4/5 | ok | 3 | $0.00124 | 2.07 | wrong: time |
| ✅ C05_abhishekam_evening | pending_review | 5/5 | ok | 2 | $0.00101 | 1.57 |  |
| ✅ C06_consult_tamil_afternoon | pending_review | 6/6 | ok | 2 | $0.00099 | 3.0 |  |
| ✅ C07_missing_everything | needs_info | 2/2 | ok | 0 | $0.00042 | 1.21 |  |
| ✅ C08_missing_date | needs_info | 5/5 | ok | 0 | $0.00035 | 0.75 |  |
| ✅ C09_missing_location | needs_info | 5/5 | ok | 0 | $0.00034 | 0.69 |  |
| ✅ C10_home_city_from_profile | pending_review | 6/6 | ok | 3 | $0.00135 | 2.13 |  |
| ✅ C11_travel_beyond_radius | pending_review | 6/6 | ok | 0 | $0.00089 | 1.4 |  |
| ✅ C12_travel_fee_waterbury | pending_review | 6/6 | ok | 3 | $0.00121 | 1.97 |  |
| ✅ C13_travel_priest_limit | pending_review | 7/7 | ok | 3 | $0.00138 | 2.25 |  |
| ✅ C14_time_off_telugu | pending_review | 6/6 | ok | 3 | $0.00145 | 1.98 |  |
| ❌ C15_diwali_conflict | pending_review | 4/5 | ok | 3 | $0.00137 | 1.62 | wrong: time |
| ❌ C16_seeded_booking_conflict | pending_review | 4/5 | fail | 3 | $0.00109 | 1.5 | wrong: time; pr_dube 2026-10-31 07:30: outside window 11:00-11:00; pr_sharma 2026-10-31 07:30: outside window 11:00-11:00; pr_sharma 2026-10-31 07:30: priest not allowed; pr_iyer 2026-10-31 07:30: outside window 11:00-11 |
| ✅ C17_unavailable_service | needs_info | 2/2 | ok | 0 | $0.00037 | 0.93 |  |
| ✅ C18_contradictory_location | pending_review | 5/5 | ok | 3 | $0.00144 | 2.19 |  |
| ✅ C19_contradictory_dates | pending_review | 5/5 | ok | 3 | $0.00126 | 2.73 |  |
| ✅ C20_accessibility_naming | pending_review | 8/8 | ok | 3 | $0.00123 | 2.52 |  |
| ✅ C21_language_unavailable | pending_review | 5/5 | ok | 0 | $0.00091 | 1.53 |  |
| ✅ C22_past_date | needs_info | 3/3 | ok | 0 | $0.00034 | 0.85 |  |
| ✅ C23_short_notice_griha | pending_review | 6/6 | ok | 0 | $0.00104 | 3.71 |  |
| ✅ C24_ambiguous_time | pending_review | 5/5 | ok | 3 | $0.00122 | 1.67 |  |
| ❌ C25_time_range_tamil | pending_review | 6/7 | fail | 0 | $0.00165 | 2.7 | wrong: time; expected at least one valid option, got none |
| ✅ C26_afternoon_griha | pending_review | 6/6 | ok | 2 | $0.00107 | 1.51 |  |
| ❌ C27_archana_exact_morning | pending_review | 4/5 | fail | 3 | $0.00109 | 1.42 | wrong: time; pr_dube 2026-11-03 08:30: outside window 08:00-08:00 |
