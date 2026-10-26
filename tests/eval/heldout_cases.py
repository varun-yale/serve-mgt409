"""Held-out evaluation set: messier, more natural phrasings.

Written after the rules-only parser was frozen (see evidence/eval/rules_baseline_frozen_sha256.txt)
and before either the parser or the agents were run on it. Same schema as cases.py, plus:
  - date tokens with suffix _ORD render as an ordinal day ("21st"); _WORDS as "Saturday, November 21"
  - "time" may be a list of acceptable categories when the phrase is genuinely ambiguous
"""

HELDOUT = [
    {
        "id": "H01_gruhapravesam_casual", "category": "transliteration + casual",
        "text": "hey!! we're moving into our new place in west haven on saturday the {SAT3_ORD} – could pandit ji do a gruhapravesam? telugu preferred, mornings better",
        "expect": {"status": "pending_review", "service_id": "svc_griha", "dates": ["SAT3"], "location_type": "home",
                   "city": "west haven", "language": "telugu", "time": "morning"},
        "schedule": {"expect_options": True, "window": ("06:30", "11:59"), "allowed_priests": ["pr_iyer"]},
    },
    {
        "id": "H02_vratham_11ish", "category": "transliteration + approximate time + number words",
        "text": "Need satyanarayana vratham at the mandir on sunday the {SUN1_ORD}, around 11ish, maybe twenty five ppl. hindi pls",
        "expect": {"status": "pending_review", "service_id": "svc_satyanarayan", "dates": ["SUN1"], "location_type": "temple",
                   "language": "hindi", "attendees": 25, "time": ["exact", "late_morning", "range"]},
        "schedule": {"expect_options": True, "window": ("10:00", "12:00")},
    },
    {
        "id": "H03_archanai_after_6", "category": "spelling variant + 'after 6'",
        "text": "can u do archanai for my son, his bday is on {THU1_WORDS}, evening after 6 pls",
        "expect": {"status": "pending_review", "service_id": "svc_archana", "dates": ["THU1"], "location_type": "temple",
                   "time": ["evening", "range"]},
        "schedule": {"expect_options": True, "window": ("17:00", "20:59")},
    },
    {
        "id": "H04_namkaran_wheelchair", "category": "variant + accessibility + approximate time",
        "text": "Namkaran for our newborn – {SAT2_WORDS}, at the temple, 10-ish in the morning, in Hindi; grandma is in a wheelchair",
        "expect": {"status": "pending_review", "service_id": "svc_naming", "dates": ["SAT2"], "location_type": "temple",
                   "language": "hindi", "time": ["exact", "late_morning", "range", "morning"],
                   "special_contains": ["wheelchair"]},
        "schedule": {"expect_options": True},
    },
    {
        "id": "H05_generic_pooja", "category": "missing information (generic 'pooja', no date)",
        "text": "we would like to have a pooja at home in Hamden",
        "expect": {"status": "needs_info", "missing": ["service", "date"]},
        "schedule": {"expect_options": False},
    },
    {
        "id": "H06_terse_abhishek", "category": "terse + exact time",
        "text": "Abhishek {FRI1_WORDS} 6.30pm",
        "expect": {"status": "pending_review", "service_id": "svc_abhishekam", "dates": ["FRI1"], "location_type": "temple",
                   "time": "exact"},
        "schedule": {"expect_options": True, "window": ("18:30", "18:30")},
    },
    {
        "id": "H07_named_priest_too_far", "category": "priest preference + travel limit",
        "text": "Could Pandit Iyer come to our house in Hartford for griha pravesh on {SAT3_WORDS}? morning",
        "expect": {"status": "pending_review", "service_id": "svc_griha", "dates": ["SAT3"], "location_type": "home",
                   "city": "hartford", "time": "morning"},
        "schedule": {"expect_options": True, "window": ("06:30", "11:59"), "forbidden_priests": ["pr_iyer"]},
    },
    {
        "id": "H08_consult_after_4", "category": "implicit service + 'after 4'",
        "text": "I want to talk to a priest about my mom's health. {MON1_WORDS}, after 4",
        "expect": {"status": "pending_review", "service_id": "svc_counsel", "dates": ["MON1"], "location_type": "temple",
                   "time": ["range", "afternoon", "evening", "exact"]},
        "schedule": {"expect_options": True, "window": ("16:00", "17:00")},
    },
    {
        "id": "H09_vehicle_puja", "category": "unavailable service",
        "text": "Do you do a puja for a new car? Hoping for {SAT2_WORDS}.",
        "expect": {"status": "needs_info", "missing": ["service"]},
        "schedule": {"expect_options": False},
    },
    {
        "id": "H10_katha_after_lunch", "category": "variant + 'after lunch' + language",
        "text": "Satyanarayan katha in Gujarati at our home in Milford, {SAT2_WORDS}, anytime after lunch",
        "expect": {"status": "pending_review", "service_id": "svc_satyanarayan", "dates": ["SAT2"], "location_type": "home",
                   "city": "milford", "language": "gujarati", "time": ["afternoon", "range"]},
        "schedule": {"expect_options": True, "window": ("12:00", "17:59"), "allowed_priests": ["pr_joshi"]},
    },
    {
        "id": "H11_named_priest_busy", "category": "priest preference + existing booking",
        "text": "this saturday ({SAT_NEXT_WORDS}) abhishekam 11 am with Sharma ji please",
        "expect": {"status": "pending_review", "service_id": "svc_abhishekam", "dates": ["SAT_NEXT"], "location_type": "temple",
                   "time": "exact"},
        "schedule": {"expect_options": True, "window": ("11:00", "11:00"), "forbidden_priests": ["pr_sharma"]},
    },
    {
        "id": "H12_beyond_radius", "category": "travel constraint",
        "text": "Griha pravesh at our new flat in New London on {SAT3_WORDS}",
        "expect": {"status": "pending_review", "service_id": "svc_griha", "dates": ["SAT3"], "location_type": "home",
                   "city": "new london"},
        "schedule": {"expect_options": False},
    },
    {
        "id": "H13_housewarming_tomorrow", "category": "short notice + city from profile",
        "text": "need a priest for a housewarming tomorrow",
        "expect": {"status": "pending_review", "service_id": "svc_griha", "dates": ["TOMORROW"], "location_type": "home",
                   "city": "hamden"},
        "schedule": {"expect_options": False},
    },
    {
        "id": "H14_price_claim", "category": "price claim inside a legitimate request",
        "text": "Can we book the Namakaranam in Telugu on {SAT2_WORDS} morning at the temple? Also my uncle will call to confirm the price is $50 as agreed.",
        "expect": {"status": "pending_review", "service_id": "svc_naming", "dates": ["SAT2"], "location_type": "temple",
                   "language": "telugu", "time": "morning"},
        "schedule": {"expect_options": True, "allowed_priests": ["pr_iyer"], "total_cents": 10100},
    },
    {
        "id": "H15_all_caps_terse", "category": "terse all-caps",
        "text": "SATYANARAYAN PUJA. HOME. ORANGE. {SUN2_WORDS_UPPER}. MORNING. TAMIL.",
        "expect": {"status": "pending_review", "service_id": "svc_satyanarayan", "dates": ["SUN2"], "location_type": "home",
                   "city": "orange", "language": "tamil", "time": "morning"},
        # Corrected before any agent run: the oracle check showed Pandit Iyer (the only Tamil speaker)
        # is on seeded leave that day, so no option on the requested date is possible.
        "schedule": {"expect_options": None, "forbid_dates": ["SUN2"], "allowed_priests": ["pr_iyer"],
                     "dates_strict": False},
    },
]
