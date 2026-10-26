# Evaluation: baseline_phase1

- Run at: 2026-10-25T21:11:22  ·  model requested: `gpt-6-luna`  ·  profile: `default`
- Cases passed (all fields + scheduling correct): **21/27**
- Field accuracy overall: **95.9%**  ·  scheduling correct: **22/27**
- Agent proposals rejected by rules engine: 0  ·  bookings created by agents: 0  ·  pipeline errors: 0
- Latency per request (s): mean 13.6, median 12.72, p90 19.41, max 24.71
- Tokens: input 210,093 (cached 97,013, cache-write 54,637), output 20,229; model requests 139, tool calls 160
- Cost (list price): total $0.023759, mean per request $0.000880

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
| ✅ C01_griha_telugu_hamden | pending_review | 9/9 | ok | 2 | $0.00111 | 19.41 |  |
| ❌ C02_satya_late_morning_hindi | pending_review | 6/7 | fail | 3 | $0.00121 | 16.1 | wrong: time; pr_dube 2026-11-01 07:00: outside window 10:00-11:59; pr_joshi 2026-11-01 08:00: outside window 10:00-11:59; pr_sharma 2026-11-01 07:30: outside window 10:00-11:59 |
| ✅ C03_naming_gujarati_unqualified | pending_review | 6/6 | ok | 0 | $0.00071 | 15.74 |  |
| ❌ C04_archana_exact_evening | pending_review | 4/5 | fail | 3 | $0.00099 | 15.82 | wrong: time; pr_dube 2026-11-05 18:00: outside window 18:30-18:30; pr_sharma 2026-11-05 18:00: outside window 18:30-18:30 |
| ✅ C05_abhishekam_evening | pending_review | 5/5 | ok | 2 | $0.00085 | 11.6 |  |
| ✅ C06_consult_tamil_afternoon | pending_review | 6/6 | ok | 2 | $0.00095 | 12.72 |  |
| ✅ C07_missing_everything | needs_info | 2/2 | ok | 0 | $0.00041 | 5.11 |  |
| ✅ C08_missing_date | needs_info | 5/5 | ok | 0 | $0.00021 | 3.83 |  |
| ✅ C09_missing_location | needs_info | 5/5 | ok | 0 | $0.00021 | 7.14 |  |
| ✅ C10_home_city_from_profile | pending_review | 6/6 | ok | 3 | $0.00122 | 19.84 |  |
| ✅ C11_travel_beyond_radius | pending_review | 6/6 | ok | 0 | $0.00076 | 12.45 |  |
| ✅ C12_travel_fee_waterbury | pending_review | 6/6 | ok | 3 | $0.00081 | 12.12 |  |
| ✅ C13_travel_priest_limit | pending_review | 7/7 | ok | 3 | $0.00121 | 19.22 |  |
| ✅ C14_time_off_telugu | pending_review | 6/6 | ok | 0 | $0.00081 | 11.98 |  |
| ❌ C15_diwali_conflict | pending_review | 4/5 | ok | 3 | $0.00133 | 18.25 | wrong: time |
| ❌ C16_seeded_booking_conflict | pending_review | 4/5 | fail | 3 | $0.00103 | 14.34 | wrong: time; pr_dube 2026-10-31 07:30: outside window 11:00-11:00; pr_sharma 2026-10-31 07:30: outside window 11:00-11:00; pr_sharma 2026-10-31 07:30: priest not allowed; pr_iyer 2026-10-31 07:30: outside window 11:00-11 |
| ✅ C17_unavailable_service | needs_info | 2/2 | ok | 0 | $0.00023 | 5.23 |  |
| ✅ C18_contradictory_location | pending_review | 5/5 | ok | 3 | $0.00139 | 20.21 |  |
| ✅ C19_contradictory_dates | pending_review | 5/5 | ok | 3 | $0.00106 | 15.49 |  |
| ✅ C20_accessibility_naming | pending_review | 8/8 | ok | 3 | $0.00106 | 11.87 |  |
| ✅ C21_language_unavailable | pending_review | 5/5 | ok | 0 | $0.00083 | 12.57 |  |
| ✅ C22_past_date | needs_info | 3/3 | ok | 0 | $0.00030 | 5.78 |  |
| ✅ C23_short_notice_griha | pending_review | 6/6 | ok | 0 | $0.00108 | 24.71 |  |
| ✅ C24_ambiguous_time | pending_review | 5/5 | ok | 3 | $0.00098 | 11.61 |  |
| ❌ C25_time_range_tamil | pending_review | 6/7 | fail | 0 | $0.00117 | 16.84 | wrong: time; expected at least one valid option, got none |
| ✅ C26_afternoon_griha | pending_review | 6/6 | ok | 2 | $0.00077 | 14.9 |  |
| ❌ C27_archana_exact_morning | pending_review | 4/5 | fail | 2 | $0.00107 | 12.35 | wrong: time; pr_sharma 2026-11-03 08:30: outside window 08:00-08:00 |
