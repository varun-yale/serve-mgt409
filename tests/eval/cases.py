"""SERVE evaluation set: synthetic member requests with expected outputs.

Written before any evaluation run and kept separate from the agent prompts.
Dates are tokens resolved against the evaluation day (and the seeded demo
calendar), so the suite is reproducible on any day:

  SAT_NEXT  first Saturday at least 1 day ahead (has a seeded booking for Pandit Sharma 11:00)
  SAT2      first Saturday >= 14 days ahead        SAT3  first Saturday >= 21 days ahead
  SUN1/SUN2 first Sunday   >= 7 / 14 days ahead    MON1, TUE1, THU1, FRI1  first weekday >= 7 days ahead
  TOMORROW, LAST_SUNDAY, DIWALI (seeded event date), IYER_OFF_MID (middle of Pandit Iyer's time off)

Expected fields (only the ones listed are scored):
  status            pending_review | needs_info
  is_service_request, service_id, dates (set), location_type, city, language,
  attendees, time (category: morning, late_morning, afternoon, evening, exact, range, any),
  missing (set, from the deterministic missing-info check)
  special_contains  keywords that must appear in special_requirements
Expected scheduling (checked against the final, rules-verified options):
  expect_options    True = at least one valid option required; False = no option acceptable; None = either
  window            (earliest, latest) start time every option must satisfy
  allowed_priests   every option must use one of these
  forbidden_priests no option may use these
  forbid_dates      no option may fall on these dates
  forbid_after      (date token, HH:MM) no option on that date starting at/after the time
  total_cents       every option must cost exactly this
  dates_strict      options must be on the requested dates (default True unless the case allows alternatives)
"""

CASES = [
    {
        "id": "C01_griha_telugu_hamden", "category": "normal + language + accessibility",
        "text": "Hi, we just bought a house in Hamden and would love a griha pravesh on {SAT3}, in the morning if possible. We'd like the ceremony in Telugu. About 25 guests, and my mother uses a wheelchair.",
        "expect": {"status": "pending_review", "service_id": "svc_griha", "dates": ["SAT3"], "location_type": "home",
                   "city": "hamden", "language": "telugu", "attendees": 25, "time": "morning",
                   "special_contains": ["wheelchair"]},
        "schedule": {"expect_options": True, "window": ("06:30", "11:59"), "allowed_priests": ["pr_iyer"]},
    },
    {
        "id": "C02_satya_late_morning_hindi", "category": "normal + late-morning preference",
        "text": "Could we have a Satyanarayan puja at the temple on {SUN1}, late morning please? Hindi is our language and about 20 family members will come.",
        "expect": {"status": "pending_review", "service_id": "svc_satyanarayan", "dates": ["SUN1"],
                   "location_type": "temple", "language": "hindi", "attendees": 20, "time": "late_morning"},
        "schedule": {"expect_options": True, "window": ("10:00", "11:59")},
    },
    {
        "id": "C03_naming_gujarati_unqualified", "category": "priest qualification + language",
        "text": "We'd like a Namakaranam for our son at the temple on {SAT2} in the morning, performed in Gujarati.",
        "expect": {"status": "pending_review", "service_id": "svc_naming", "dates": ["SAT2"], "location_type": "temple",
                   "language": "gujarati", "time": "morning"},
        "schedule": {"expect_options": False},  # no Gujarati-speaking priest is qualified for Namakaranam
    },
    {
        "id": "C04_archana_exact_evening", "category": "exact time",
        "text": "Please book an archana for my daughter's birthday on {THU1} at 6:30 pm.",
        "expect": {"status": "pending_review", "service_id": "svc_archana", "dates": ["THU1"], "location_type": "temple",
                   "time": "exact"},
        "schedule": {"expect_options": True, "window": ("18:30", "18:30")},
    },
    {
        "id": "C05_abhishekam_evening", "category": "evening preference",
        "text": "I'd like to sponsor an abhishekam on {FRI1} in the evening, in memory of my father.",
        "expect": {"status": "pending_review", "service_id": "svc_abhishekam", "dates": ["FRI1"], "location_type": "temple",
                   "time": "evening"},
        "schedule": {"expect_options": True, "window": ("17:00", "20:59")},
    },
    {
        "id": "C06_consult_tamil_afternoon", "category": "afternoon + language",
        "text": "Can I meet with a priest for a consultation on {MON1} in the afternoon? I'd prefer to speak in Tamil.",
        "expect": {"status": "pending_review", "service_id": "svc_counsel", "dates": ["MON1"], "location_type": "temple",
                   "language": "tamil", "time": "afternoon"},
        "schedule": {"expect_options": True, "window": ("12:00", "16:59"), "allowed_priests": ["pr_iyer"]},
    },
    {
        "id": "C07_missing_everything", "category": "missing information",
        "text": "Hello, I'd like to book something for my family soon. What do you suggest?",
        "expect": {"status": "needs_info", "missing": ["service", "date"]},
        "schedule": {"expect_options": False},
    },
    {
        "id": "C08_missing_date", "category": "missing information",
        "text": "We want a Satyanarayan puja at our home in Orange. Please let me know.",
        "expect": {"status": "needs_info", "service_id": "svc_satyanarayan", "location_type": "home", "city": "orange",
                   "missing": ["date"]},
        "schedule": {"expect_options": False},
    },
    {
        "id": "C09_missing_location", "category": "missing information",
        "text": "Satyanarayan puja on {SUN1} in the morning, in Hindi.",
        "expect": {"status": "needs_info", "service_id": "svc_satyanarayan", "dates": ["SUN1"], "language": "hindi",
                   "missing": ["location"]},
        "schedule": {"expect_options": False},
    },
    {
        "id": "C10_home_city_from_profile", "category": "missing information (resolvable from profile)",
        "text": "We'd like a griha pravesh at our new home on {SAT3}, morning.",
        "expect": {"status": "pending_review", "service_id": "svc_griha", "dates": ["SAT3"], "location_type": "home",
                   "city": "hamden", "time": "morning"},
        "schedule": {"expect_options": True, "window": ("06:30", "11:59")},
    },
    {
        "id": "C11_travel_beyond_radius", "category": "travel constraint",
        "text": "Could a priest come to our home in Stamford for a Satyanarayan puja on {SAT2} in the afternoon?",
        "expect": {"status": "pending_review", "service_id": "svc_satyanarayan", "dates": ["SAT2"], "location_type": "home",
                   "city": "stamford", "time": "afternoon"},
        "schedule": {"expect_options": False},  # Stamford is 46 miles; service radius is 45
    },
    {
        "id": "C12_travel_fee_waterbury", "category": "travel fee",
        "text": "Griha pravesh at our home in Waterbury on {SAT3}, any time that works.",
        "expect": {"status": "pending_review", "service_id": "svc_griha", "dates": ["SAT3"], "location_type": "home",
                   "city": "waterbury", "time": "any"},
        "schedule": {"expect_options": True, "total_cents": 25550},  # 28 miles -> 3 miles x $1.50
    },
    {
        "id": "C13_travel_priest_limit", "category": "travel constraint (per-priest)",
        "text": "We'd like a Satyanarayan puja at our home in Middletown on {SAT2}, in the morning, in Hindi.",
        "expect": {"status": "pending_review", "service_id": "svc_satyanarayan", "dates": ["SAT2"], "location_type": "home",
                   "city": "middletown", "language": "hindi", "time": "morning"},
        "schedule": {"expect_options": True, "window": ("06:30", "11:59"), "forbidden_priests": ["pr_dube"]},
    },
    {
        "id": "C14_time_off_telugu", "category": "date conflict (priest time off)",
        "text": "Abhishekam on {IYER_OFF_MID} in the morning, conducted in Telugu please.",
        "expect": {"status": "pending_review", "service_id": "svc_abhishekam", "dates": ["IYER_OFF_MID"],
                   "location_type": "temple", "language": "telugu", "time": "morning"},
        "schedule": {"expect_options": None, "forbid_dates": ["IYER_OFF_MID"], "allowed_priests": ["pr_iyer"],
                     "dates_strict": False},
    },
    {
        "id": "C15_diwali_conflict", "category": "date conflict (temple event)",
        "text": "Archana on {DIWALI} at 6 pm for our family, please.",
        "expect": {"status": "pending_review", "service_id": "svc_archana", "dates": ["DIWALI"], "location_type": "temple",
                   "time": "exact"},
        "schedule": {"expect_options": None, "forbid_after": ("DIWALI", "16:00"), "dates_strict": False},
    },
    {
        "id": "C16_seeded_booking_conflict", "category": "date conflict (existing bookings)",
        "text": "Abhishekam on {SAT_NEXT} at 11 am, please.",
        "expect": {"status": "pending_review", "service_id": "svc_abhishekam", "dates": ["SAT_NEXT"],
                   "location_type": "temple", "time": "exact"},
        "schedule": {"expect_options": True, "window": ("11:00", "11:00"), "allowed_priests": ["pr_dube"]},
    },
    {
        "id": "C17_unavailable_service", "category": "unavailable service",
        "text": "Can the temple perform our wedding ceremony (vivah) on {SAT3}? About 150 guests.",
        "expect": {"status": "needs_info", "missing": ["service"]},
        "schedule": {"expect_options": False},
    },
    {
        "id": "C18_contradictory_location", "category": "contradictory request",
        "text": "We'd like a griha pravesh performed in the temple hall on {SAT3} in the morning.",
        "expect": {"status": "pending_review", "service_id": "svc_griha", "dates": ["SAT3"], "location_type": "home",
                   "time": "morning"},
        "schedule": {"expect_options": None},
    },
    {
        "id": "C19_contradictory_dates", "category": "contradictory request (self-correction)",
        "text": "Satyanarayan puja at the temple on {SAT2} — sorry, I meant {SUN2} — in the morning.",
        "expect": {"status": "pending_review", "service_id": "svc_satyanarayan", "dates": ["SUN2"],
                   "location_type": "temple", "time": "morning"},
        "schedule": {"expect_options": True, "window": ("06:30", "11:59")},
    },
    {
        "id": "C20_accessibility_naming", "category": "accessibility + guests",
        "text": "Namakaranam for our granddaughter at the temple on {SAT2} in the morning, in Hindi. About 30 guests; my father uses a walker and will need a chair near the front.",
        "expect": {"status": "pending_review", "service_id": "svc_naming", "dates": ["SAT2"], "location_type": "temple",
                   "language": "hindi", "attendees": 30, "time": "morning", "special_contains": ["walker"]},
        "schedule": {"expect_options": True, "window": ("06:30", "11:59")},
    },
    {
        "id": "C21_language_unavailable", "category": "language unavailable",
        "text": "Satyanarayan puja at the temple on {SUN2} in Bengali, please.",
        "expect": {"status": "pending_review", "service_id": "svc_satyanarayan", "dates": ["SUN2"],
                   "location_type": "temple", "language": "bengali"},
        "schedule": {"expect_options": False},
    },
    {
        "id": "C22_past_date", "category": "invalid date",
        "text": "I'd like an archana on {LAST_SUNDAY} at 8 am.",
        "expect": {"status": "needs_info", "service_id": "svc_archana", "missing": ["date"]},
        "schedule": {"expect_options": False},
    },
    {
        "id": "C23_short_notice_griha", "category": "lead-time policy",
        "text": "Can we do a griha pravesh at our home in Hamden {TOMORROW} morning?",
        "expect": {"status": "pending_review", "service_id": "svc_griha", "dates": ["TOMORROW"], "location_type": "home",
                   "city": "hamden", "time": "morning"},
        "schedule": {"expect_options": False},  # needs 5 days' notice; alternatives within 3 days also too soon
    },
    {
        "id": "C24_ambiguous_time", "category": "ambiguous time",
        "text": "Satyanarayan puja at the temple on {SUN2}, whatever time the priest is free.",
        "expect": {"status": "pending_review", "service_id": "svc_satyanarayan", "dates": ["SUN2"],
                   "location_type": "temple", "time": "any"},
        "schedule": {"expect_options": True},
    },
    {
        "id": "C25_time_range_tamil", "category": "explicit time range + language",
        "text": "Satyanarayan puja at our home in Branford on {SAT2}, starting between 10 and 11:30 am, in Tamil.",
        "expect": {"status": "pending_review", "service_id": "svc_satyanarayan", "dates": ["SAT2"], "location_type": "home",
                   "city": "branford", "language": "tamil", "time": "range"},
        "schedule": {"expect_options": True, "window": ("10:00", "11:30"), "allowed_priests": ["pr_iyer"]},
    },
    {
        "id": "C26_afternoon_griha", "category": "afternoon + home",
        "text": "Griha pravesh at our home in Woodbridge on {SUN2} in the afternoon.",
        "expect": {"status": "pending_review", "service_id": "svc_griha", "dates": ["SUN2"], "location_type": "home",
                   "city": "woodbridge", "time": "afternoon"},
        "schedule": {"expect_options": True, "window": ("12:00", "16:59")},
    },
    {
        "id": "C27_archana_exact_morning", "category": "exact time",
        "text": "Archana on {TUE1} at 8am please, for my exam results.",
        "expect": {"status": "pending_review", "service_id": "svc_archana", "dates": ["TUE1"], "location_type": "temple",
                   "time": "exact"},
        "schedule": {"expect_options": True, "window": ("08:00", "08:00")},
    },
]
