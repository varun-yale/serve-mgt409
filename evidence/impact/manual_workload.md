# Scheduling workload behind each request (deterministic, reproducible)

Requests analyzed: 35 (complete requests from the 27 main + 15 held-out cases; expected answers used).

| Mean per request | Value |
|---|---|
| qualified priests | 3.5 |
| qualified and language ok | 2.5 |
| calendars to open | 2.5 |
| candidate slots to test | 30.8 |
| rule checks | 276.9 |
| home requests needing a travel lookup | 15 of 35 |
| requests whose correct answer is 'no availability' | 9 of 35 |

**With SERVE:** Agents + rules engine perform these checks automatically (measured ~10.5 s, $0.00056 per request, optimized profile); the administrator reviews evidence and clicks Approve.

**ESTIMATE (assumption, not measured):** 1 minute per priest-day calendar opened + 0.25 min per candidate slot tested + 3 min travel lookup if home + 4 min read/reply → mean ≈ 15.5 min per request.

| Case | Qualified priests | + language | Calendars | Candidate slots | Rule checks | Valid options |
|---|---|---|---|---|---|---|
| C01_griha_telugu_hamden | 3 | 1 | 1 | 11 | 99 | 5 |
| C02_satya_late_morning_hindi | 4 | 3 | 3 | 12 | 108 | 12 |
| C03_naming_gujarati_unqualified | 3 | 0 | 0 | 0 | 0 | 0 |
| C04_archana_exact_evening | 4 | 4 | 4 | 4 | 36 | 3 |
| C05_abhishekam_evening | 3 | 3 | 3 | 3 | 27 | 2 |
| C06_consult_tamil_afternoon | 4 | 1 | 1 | 2 | 18 | 2 |
| C10_home_city_from_profile | 3 | 3 | 3 | 33 | 297 | 16 |
| C11_travel_beyond_radius | 4 | 4 | 4 | 112 | 1008 | 0 |
| C12_travel_fee_waterbury | 3 | 3 | 3 | 84 | 756 | 27 |
| C13_travel_priest_limit | 4 | 3 | 3 | 33 | 297 | 10 |
| C14_time_off_telugu | 3 | 1 | 1 | 3 | 27 | 0 |
| C15_diwali_conflict | 4 | 4 | 4 | 16 | 144 | 4 |
| C16_seeded_booking_conflict | 3 | 3 | 3 | 3 | 27 | 1 |
| C18_contradictory_location | 3 | 3 | 3 | 84 | 756 | 0 |
| C19_contradictory_dates | 4 | 4 | 4 | 44 | 396 | 20 |
| C20_accessibility_naming | 3 | 2 | 2 | 22 | 198 | 19 |
| C21_language_unavailable | 4 | 0 | 0 | 0 | 0 | 0 |
| C23_short_notice_griha | 3 | 3 | 3 | 84 | 756 | 0 |
| C24_ambiguous_time | 4 | 4 | 4 | 112 | 1008 | 27 |
| C25_time_range_tamil | 4 | 1 | 1 | 4 | 36 | 2 |
| C26_afternoon_griha | 3 | 3 | 3 | 30 | 270 | 5 |
| C27_archana_exact_morning | 4 | 4 | 4 | 4 | 36 | 2 |
| H01_gruhapravesam_casual | 3 | 1 | 1 | 11 | 99 | 5 |
| H02_vratham_11ish | 4 | 3 | 3 | 15 | 135 | 13 |
| H03_archanai_after_6 | 4 | 4 | 4 | 8 | 72 | 6 |
| H04_namkaran_wheelchair | 3 | 2 | 2 | 56 | 504 | 27 |
| H06_terse_abhishek | 3 | 3 | 3 | 3 | 27 | 2 |
| H07_named_priest_too_far | 3 | 3 | 3 | 33 | 297 | 3 |
| H08_consult_after_4 | 4 | 4 | 4 | 12 | 108 | 7 |
| H10_katha_after_lunch | 4 | 1 | 1 | 12 | 108 | 12 |
| H11_named_priest_busy | 3 | 3 | 3 | 3 | 27 | 1 |
| H12_beyond_radius | 3 | 3 | 3 | 84 | 756 | 0 |
| H13_housewarming_tomorrow | 3 | 3 | 3 | 84 | 756 | 0 |
| H14_price_claim | 3 | 1 | 1 | 28 | 252 | 18 |
| H15_all_caps_terse | 4 | 1 | 1 | 28 | 252 | 0 |
