"""SQLite schema and demonstration seed data.

All people, priests, bookings and the temple itself are fictional demonstration
data. Dates are generated relative to the day the database is first seeded so
the calendar is always current; reseed with `python -m backend.db --reset`.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import date, datetime, timedelta

from .config import DATA_DIR, DB_PATH, DEMO_MEMBER_ID, TIMEZONE

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS members (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  home_city TEXT,
  joined_on TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS services (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  aliases TEXT NOT NULL,              -- JSON list of other names members use
  category TEXT NOT NULL,
  price_cents INTEGER NOT NULL,
  price_label TEXT NOT NULL,
  duration_minutes INTEGER NOT NULL,
  duration_label TEXT NOT NULL,
  scheduling TEXT NOT NULL CHECK (scheduling IN ('fixed_slots', 'request_based')),
  location_mode TEXT NOT NULL CHECK (location_mode IN ('temple', 'home', 'either')),
  temple_room TEXT,
  slot_times TEXT,                    -- JSON list of HH:MM start times for fixed-slot services
  min_lead_days INTEGER NOT NULL,
  recommended_lead_days INTEGER,
  summary TEXT NOT NULL,
  description TEXT NOT NULL,
  location_label TEXT NOT NULL,
  things_to_know TEXT NOT NULL,       -- JSON list
  popular INTEGER NOT NULL DEFAULT 0,
  enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS priests (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  title TEXT NOT NULL,
  max_travel_miles INTEGER NOT NULL,
  bio TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS priest_languages (
  priest_id TEXT NOT NULL REFERENCES priests(id),
  language TEXT NOT NULL,
  PRIMARY KEY (priest_id, language)
);

CREATE TABLE IF NOT EXISTS priest_qualifications (
  priest_id TEXT NOT NULL REFERENCES priests(id),
  service_id TEXT NOT NULL REFERENCES services(id),
  PRIMARY KEY (priest_id, service_id)
);

-- Recurring weekly availability. weekday: 0 = Monday ... 6 = Sunday.
CREATE TABLE IF NOT EXISTS priest_availability (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  priest_id TEXT NOT NULL REFERENCES priests(id),
  weekday INTEGER NOT NULL CHECK (weekday BETWEEN 0 AND 6),
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS priest_time_off (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  priest_id TEXT NOT NULL REFERENCES priests(id),
  start_date TEXT NOT NULL,
  end_date TEXT NOT NULL,
  reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS travel_zones (
  city TEXT PRIMARY KEY,              -- lower-case town name, Connecticut
  display_name TEXT NOT NULL,
  miles INTEGER NOT NULL,
  drive_minutes INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS policies (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  date TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  location TEXT NOT NULL,
  summary TEXT NOT NULL,
  description TEXT NOT NULL,
  image TEXT NOT NULL,
  volunteer_opportunity_ids TEXT NOT NULL,   -- JSON list
  blocks_all_priests INTEGER NOT NULL DEFAULT 0,
  blocked_priest_id TEXT REFERENCES priests(id)
);

CREATE TABLE IF NOT EXISTS service_requests (
  id TEXT PRIMARY KEY,
  member_id TEXT NOT NULL REFERENCES members(id),
  source TEXT NOT NULL CHECK (source IN ('ai_request', 'request_form', 'slot_picker')),
  raw_text TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN
    ('processing', 'pending_review', 'needs_info', 'approved', 'rejected', 'failed', 'cancelled')),
  intake_json TEXT,
  recommendation_json TEXT,
  missing_info TEXT,                  -- JSON list
  risk_flags TEXT,                    -- JSON: sanitization, injection patterns, output filtering
  member_message TEXT,
  admin_note TEXT,
  error TEXT,
  booking_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS bookings (
  id TEXT PRIMARY KEY,
  request_id TEXT UNIQUE REFERENCES service_requests(id),
  member_id TEXT NOT NULL REFERENCES members(id),
  service_id TEXT NOT NULL REFERENCES services(id),
  priest_id TEXT NOT NULL REFERENCES priests(id),
  date TEXT NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL,
  location_type TEXT NOT NULL CHECK (location_type IN ('temple', 'home')),
  city TEXT,
  language TEXT,
  base_price_cents INTEGER NOT NULL,
  travel_fee_cents INTEGER NOT NULL,
  total_cents INTEGER NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled', 'completed')),
  payment TEXT NOT NULL DEFAULT 'unpaid',
  approved_by TEXT,
  created_at TEXT NOT NULL
);
-- Backstop against two confirmed bookings starting at the same time for one priest.
CREATE UNIQUE INDEX IF NOT EXISTS ux_bookings_priest_start
  ON bookings (priest_id, date, start_time) WHERE status = 'confirmed';

CREATE TABLE IF NOT EXISTS approvals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  request_id TEXT NOT NULL REFERENCES service_requests(id),
  decision TEXT NOT NULL CHECK (decision IN ('approved', 'approved_edited', 'rejected', 'needs_info', 'blocked')),
  admin_name TEXT NOT NULL,
  note TEXT,
  slot_json TEXT,
  decided_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id TEXT PRIMARY KEY,
  request_id TEXT REFERENCES service_requests(id),
  agent TEXT NOT NULL,
  model TEXT NOT NULL,
  response_model TEXT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  latency_ms INTEGER,
  status TEXT NOT NULL,
  error TEXT,
  model_requests INTEGER,
  input_tokens INTEGER,
  cached_input_tokens INTEGER,
  cache_write_tokens INTEGER,
  output_tokens INTEGER,
  reasoning_tokens INTEGER,
  tool_calls INTEGER,
  cost_usd REAL,
  cost_breakdown TEXT,
  output_json TEXT,
  provider TEXT,                      -- x-portkey-provider of each response
  portkey_target TEXT,                -- x-portkey-last-used-option-index (config route)
  portkey_cache TEXT,                 -- x-portkey-cache-status per HTTP response
  portkey_cache_hits INTEGER,
  http_log TEXT
);

CREATE TABLE IF NOT EXISTS tool_calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL REFERENCES agent_runs(id),
  request_id TEXT,
  agent TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  args_json TEXT NOT NULL,
  result_summary TEXT NOT NULL,
  ok INTEGER NOT NULL,
  duration_ms INTEGER NOT NULL,
  called_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  request_id TEXT,
  booking_id TEXT,
  details_json TEXT
);
"""


def now_iso() -> str:
    return datetime.now(TIMEZONE).isoformat(timespec="seconds")


def today() -> date:
    return datetime.now(TIMEZONE).date()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # One connection per request or pipeline run; FastAPI may open and use it on different
    # worker threads, so cross-thread use is allowed (it is never shared concurrently).
    conn = sqlite3.connect(DB_PATH, timeout=10, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def audit(conn: sqlite3.Connection, actor: str, action: str, request_id: str | None = None,
          booking_id: str | None = None, details: dict | None = None) -> None:
    conn.execute(
        "INSERT INTO audit_events (ts, actor, action, request_id, booking_id, details_json) VALUES (?,?,?,?,?,?)",
        (now_iso(), actor, action, request_id, booking_id, json.dumps(details or {}, default=str)),
    )


# ---------------------------------------------------------------------------
# Seed data (fictional)
# ---------------------------------------------------------------------------

MEMBERS = [
    (DEMO_MEMBER_ID, "Arjun Patel", "arjun.patel@example.com", "hamden", "March 2021"),
    ("mem_meena", "Meena Iyer", "meena.iyer@example.com", "new haven", "June 2015"),
    ("mem_sanjay", "Sanjay Rao", "sanjay.rao@example.com", "west haven", "January 2018"),
    ("mem_lata", "Lata Desai", "lata.desai@example.com", "orange", "May 2020"),
    ("mem_vikram", "Vikram Shah", "vikram.shah@example.com", "milford", "October 2022"),
]

SERVICES = [
    dict(
        id="svc_archana", name="Archana", aliases=["archanai", "name offering", "birthday archana"],
        category="Daily Services", price_cents=2500, price_label="$25", duration_minutes=15,
        duration_label="Approx. 15 minutes", scheduling="fixed_slots", location_mode="temple",
        temple_room="Main Hall", slot_times=["08:00", "08:30", "18:00", "18:30"], min_lead_days=0,
        recommended_lead_days=None, popular=1,
        summary="A short personal offering with your name and intention.",
        description="A brief personal offering performed by a priest, who recites your name, birth star, and intention. Commonly requested for birthdays, anniversaries, exam results, or simply gratitude.",
        location_label="Main Hall",
        things_to_know=["Arrive about ten minutes early and check in at the front desk.",
                        "Bring the full name and birth star of anyone being named, if you know it.",
                        "Offerings of flowers or fruit are welcome but never required."],
    ),
    dict(
        id="svc_abhishekam", name="Abhishekam", aliases=["abhishek", "abishekam", "deity bathing"],
        category="Daily Services", price_cents=5100, price_label="$51", duration_minutes=30,
        duration_label="Approx. 30 minutes", scheduling="fixed_slots", location_mode="temple",
        temple_room="Main Hall", slot_times=["07:30", "11:00", "18:30"], min_lead_days=0,
        recommended_lead_days=None, popular=1,
        summary="A ceremonial bathing ritual with water, milk, and honey.",
        description="A ceremonial bathing of the deity accompanied by chanting. Families often sponsor an abhishekam to mark a milestone or dedicate the merit to a relative.",
        location_label="Main Hall",
        things_to_know=["Seating is limited to about eight people in the inner hall.",
                        "The ritual runs on a fixed schedule and begins promptly.",
                        "Prasad is distributed to your party afterward."],
    ),
    dict(
        id="svc_satyanarayan", name="Satyanarayan Puja", aliases=["satyanarayana", "satyanarayan katha", "full moon puja"],
        category="Special Pujas", price_cents=15100, price_label="$151", duration_minutes=90,
        duration_label="Approx. 90 minutes", scheduling="request_based", location_mode="either",
        temple_room="Main Hall", slot_times=None, min_lead_days=3, recommended_lead_days=7, popular=1,
        summary="A full household puja, usually sponsored by one family.",
        description="A longer ceremony traditionally performed on a full moon or to mark the fulfilment of a vow. One family sponsors the puja and may invite guests; the priest will walk you through each step as it happens.",
        location_label="Main Hall or your home",
        things_to_know=["Requires scheduling — describe your preferred dates and the office confirms.",
                        "Can be performed at your home; travel beyond 25 miles adds a fee.",
                        "A materials list is shared once the date is confirmed."],
    ),
    dict(
        id="svc_griha", name="Griha Pravesh", aliases=["housewarming", "house warming", "griha pravesam", "gruhapravesam", "house blessing", "new home puja"],
        category="Life Events", price_cents=25100, price_label="Starting at $251", duration_minutes=120,
        duration_label="Approx. 2 hours", scheduling="request_based", location_mode="home",
        temple_room=None, slot_times=None, min_lead_days=5, recommended_lead_days=21, popular=0,
        summary="A house blessing performed at your new home.",
        description="A housewarming ceremony performed at your residence before you move in. Scope depends on the size of the home and which rituals you include.",
        location_label="Your home",
        things_to_know=["Please request at least three weeks ahead where possible.",
                        "Travel within 25 miles is included in the base price.",
                        "An auspicious time window will be suggested for your chosen date."],
    ),
    dict(
        id="svc_naming", name="Namakaranam", aliases=["naming ceremony", "baby naming", "namkaran", "namakarana"],
        category="Life Events", price_cents=10100, price_label="$101", duration_minutes=45,
        duration_label="Approx. 45 minutes", scheduling="request_based", location_mode="either",
        temple_room="Main Hall", slot_times=None, min_lead_days=3, recommended_lead_days=10, popular=0,
        summary="A naming ceremony for a newborn child.",
        description="A ceremony formally giving a child their name, typically held in the first weeks after birth. Families usually invite close relatives; the hall accommodates about thirty guests.",
        location_label="Main Hall or your home",
        things_to_know=["Requires scheduling — describe your preferred dates.",
                        "Let us know your expected guest count when requesting.",
                        "The hall accommodates about thirty guests."],
    ),
    dict(
        id="svc_counsel", name="Priest Consultation", aliases=["consultation", "talk to a priest", "meet a priest"],
        category="Priest Services", price_cents=0, price_label="No charge", duration_minutes=30,
        duration_label="Approx. 30 minutes", scheduling="fixed_slots", location_mode="temple",
        temple_room="Library Room", slot_times=["16:00", "16:30", "17:00"], min_lead_days=1,
        recommended_lead_days=None, popular=0,
        summary="A private conversation with a priest.",
        description="A confidential meeting to discuss a personal matter, plan a ceremony, or ask questions about practice. There is no charge for consultations.",
        location_label="Library Room",
        things_to_know=["Conversations are confidential.",
                        "Available in English, Hindi, Gujarati, and Tamil."],
    ),
]

PRIESTS = [
    ("pr_sharma", "Pandit Ramesh Sharma", "Head Priest", 40,
     "Head priest for 22 years; trained in Varanasi.",
     ["Hindi", "Sanskrit", "English"],
     ["svc_archana", "svc_abhishekam", "svc_satyanarayan", "svc_griha", "svc_naming", "svc_counsel"]),
    ("pr_dube", "Pandit Anil Dube", "Associate Priest", 20,
     "Leads the weekly Bhagavad Gita discussion.",
     ["Hindi", "Sanskrit", "English"],
     ["svc_archana", "svc_abhishekam", "svc_satyanarayan", "svc_naming", "svc_counsel"]),
    ("pr_iyer", "Pandit Venkatesh Iyer", "Priest", 35,
     "Performs South Indian (Agama) rituals.",
     ["Tamil", "Telugu", "Sanskrit", "English"],
     ["svc_archana", "svc_abhishekam", "svc_satyanarayan", "svc_griha", "svc_naming", "svc_counsel"]),
    ("pr_joshi", "Pandit Hemant Joshi", "Priest", 30,
     "Serves the Gujarati community; part-time, weekends and evenings.",
     ["Gujarati", "Hindi", "Sanskrit", "English"],
     ["svc_archana", "svc_satyanarayan", "svc_griha", "svc_counsel"]),
]

# weekday 0 = Monday
AVAILABILITY = {
    "pr_sharma": [(d, "07:00", "12:00") for d in range(0, 6)] + [(d, "16:00", "20:00") for d in range(0, 6)] + [(6, "07:00", "13:00")],
    "pr_dube": [(d, "07:00", "13:00") for d in (1, 2, 3, 4, 5, 6)] + [(d, "17:00", "21:00") for d in (1, 2, 3, 4)],
    "pr_iyer": [(d, "06:30", "12:30") for d in (0, 2, 3, 4, 5, 6)] + [(d, "15:00", "19:30") for d in (0, 2, 4, 5, 6)],
    "pr_joshi": [(d, "17:00", "21:00") for d in (0, 1, 2, 3, 4)] + [(5, "08:00", "20:00"), (6, "08:00", "18:00")],
}

TRAVEL_ZONES = [
    ("new haven", "New Haven", 3, 10), ("hamden", "Hamden", 6, 15), ("west haven", "West Haven", 5, 12),
    ("east haven", "East Haven", 6, 14), ("north haven", "North Haven", 8, 16), ("orange", "Orange", 7, 15),
    ("woodbridge", "Woodbridge", 8, 17), ("branford", "Branford", 10, 18), ("milford", "Milford", 11, 18),
    ("wallingford", "Wallingford", 14, 22), ("cheshire", "Cheshire", 15, 24), ("guilford", "Guilford", 17, 25),
    ("shelton", "Shelton", 17, 26), ("meriden", "Meriden", 20, 28), ("stratford", "Stratford", 16, 24),
    ("madison", "Madison", 22, 30), ("bridgeport", "Bridgeport", 20, 28), ("trumbull", "Trumbull", 20, 30),
    ("middletown", "Middletown", 26, 34), ("waterbury", "Waterbury", 28, 36), ("fairfield", "Fairfield", 26, 34),
    ("old saybrook", "Old Saybrook", 31, 38), ("norwalk", "Norwalk", 38, 50), ("hartford", "Hartford", 40, 52),
    ("stamford", "Stamford", 46, 60), ("new london", "New London", 50, 58),
]

POLICIES = [
    ("max_advance_days", "120", "Bookings can be made at most this many days ahead."),
    ("buffer_minutes", "30", "Minimum gap between two commitments for the same priest."),
    ("included_travel_miles", "25", "Home services within this distance (one way) have no travel fee."),
    ("travel_fee_per_mile_cents", "150", "Travel fee per mile beyond the included distance (one way)."),
    ("max_service_radius_miles", "45", "Home services beyond this distance are not offered."),
    ("home_service_earliest", "08:00", "Home services start no earlier than this."),
    ("home_service_latest_end", "20:00", "Home services must end by this time."),
    ("temple_open", "07:00", "Temple opens."),
    ("temple_close", "21:00", "Temple closes; temple services must end by this time."),
]


def _events(seed_day: date) -> list[tuple]:
    def next_weekday(wd: int, after: int = 0) -> date:
        d = seed_day + timedelta(days=after)
        return d + timedelta(days=(wd - d.weekday()) % 7)

    diwali_2026 = date(2026, 11, 8)
    diwali = diwali_2026 if diwali_2026 > seed_day else next_weekday(5, 14)
    sunday = next_weekday(6, 1)
    wednesday = next_weekday(2, 1)
    saturday = next_weekday(5, 1)
    purnima = next_weekday(4, 18)
    return [
        ("evt_diwali", "Diwali Celebration", diwali.isoformat(), "17:00", "22:00", "Main Hall & Courtyard",
         "Lamp lighting, music, and a community dinner for all ages.",
         "Our largest gathering of the year. The evening opens with a lamp lighting in the courtyard, followed by devotional music, a children's performance, and a full community dinner. Bring family and friends — no registration required.",
         "linear-gradient(135deg, #c98a21 0%, #f4cd77 100%)",
         ["vol_diwali_setup", "vol_diwali_food", "vol_diwali_cleanup"], 1, None),
        ("evt_lunch", "Sunday Community Lunch", sunday.isoformat(), "12:30", "14:00", "Community Kitchen",
         "A free vegetarian meal, served every Sunday to anyone who comes.",
         "Annadanam is at the heart of what we do. Every Sunday our kitchen volunteers prepare and serve a free vegetarian lunch. There is no cost and no expectation — come eat with us.",
         "linear-gradient(135deg, #b07f22 0%, #f8e3b4 100%)",
         ["vol_lunch_prep", "vol_lunch_serve", "vol_lunch_cleanup"], 0, None),
        ("evt_gita", "Bhagavad Gita Discussion", wednesday.isoformat(), "19:00", "20:30", "Library Room",
         "An open weekly discussion group — no preparation needed.",
         "A conversational study group working slowly through the text. Pandit Anil Dube facilitates, but the format is discussion rather than lecture. Newcomers can join at any point.",
         "linear-gradient(135deg, #2b2419 0%, #b8842a 100%)", [], 0, "pr_dube"),
        ("evt_youth", "Youth Cultural Class", saturday.isoformat(), "10:00", "12:00", "Classroom B",
         "Language, music, and dance for children ages 5–14.",
         "A weekly class rotating through language basics, devotional music, and classical dance. Taught by community volunteers. Registration is per term, but visitors may sit in on a session first.",
         "linear-gradient(135deg, #edb54c 0%, #8c6417 100%)", [], 0, None),
        ("evt_katha", "Community Satyanarayan Katha", purnima.isoformat(), "18:00", "20:30", "Main Hall",
         "An evening katha led by all of the temple's priests.",
         "The temple's priests lead a community katha followed by lamp offerings at the pond. Families are welcome to bring a diya.",
         "linear-gradient(135deg, #5a4824 0%, #d4a949 100%)", [], 1, None),
    ]


def seed(conn: sqlite3.Connection) -> None:
    seed_day = today()
    conn.execute("BEGIN")
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('seeded_on', ?)", (seed_day.isoformat(),))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('demo_notice', ?)",
                 ("All organizations, people, priests and bookings are fictional demonstration data.",))
    conn.executemany("INSERT INTO members VALUES (?,?,?,?,?)", MEMBERS)
    for s in SERVICES:
        conn.execute(
            """INSERT INTO services (id, name, aliases, category, price_cents, price_label, duration_minutes,
               duration_label, scheduling, location_mode, temple_room, slot_times, min_lead_days,
               recommended_lead_days, summary, description, location_label, things_to_know, popular, enabled)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)""",
            (s["id"], s["name"], json.dumps(s["aliases"]), s["category"], s["price_cents"], s["price_label"],
             s["duration_minutes"], s["duration_label"], s["scheduling"], s["location_mode"], s["temple_room"],
             json.dumps(s["slot_times"]) if s["slot_times"] else None, s["min_lead_days"],
             s["recommended_lead_days"], s["summary"], s["description"], s["location_label"],
             json.dumps(s["things_to_know"]), s["popular"]),
        )
    for pid, name, title, miles, bio, langs, quals in PRIESTS:
        conn.execute("INSERT INTO priests VALUES (?,?,?,?,?,1)", (pid, name, title, miles, bio))
        conn.executemany("INSERT INTO priest_languages VALUES (?,?)", [(pid, lang) for lang in langs])
        conn.executemany("INSERT INTO priest_qualifications VALUES (?,?)", [(pid, q) for q in quals])
    for pid, rows in AVAILABILITY.items():
        conn.executemany(
            "INSERT INTO priest_availability (priest_id, weekday, start_time, end_time) VALUES (?,?,?,?)",
            [(pid, *r) for r in rows],
        )
    # Pandit Iyer is away for a stretch two weeks out — a real constraint the agent must notice.
    off_start = seed_day + timedelta(days=12)
    conn.execute(
        "INSERT INTO priest_time_off (priest_id, start_date, end_date, reason) VALUES (?,?,?,?)",
        ("pr_iyer", off_start.isoformat(), (off_start + timedelta(days=4)).isoformat(), "Family travel"),
    )
    conn.executemany("INSERT INTO travel_zones VALUES (?,?,?,?)", TRAVEL_ZONES)
    conn.executemany("INSERT INTO policies VALUES (?,?,?)", POLICIES)
    for e in _events(seed_day):
        conn.execute(
            "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (*e[:9], json.dumps(e[9]), e[10], e[11]),
        )

    # Existing confirmed bookings (seeded history, not from agents) so conflicts are real.
    def nxt(wd: int, after: int) -> str:
        d = seed_day + timedelta(days=after)
        return (d + timedelta(days=(wd - d.weekday()) % 7)).isoformat()

    created = now_iso()
    seeded = [
        ("bk_seed_1", DEMO_MEMBER_ID, "svc_abhishekam", "pr_sharma", nxt(5, 1), "11:00", "11:30", "temple", None, "Sanskrit", 5100, 0),
        ("bk_seed_2", "mem_meena", "svc_satyanarayan", "pr_iyer", nxt(5, 1), "09:00", "10:30", "home", "new haven", "Tamil", 15100, 0),
        ("bk_seed_3", "mem_sanjay", "svc_griha", "pr_sharma", nxt(6, 8), "08:00", "10:00", "home", "west haven", "Hindi", 25100, 0),
        ("bk_seed_4", "mem_lata", "svc_naming", "pr_dube", nxt(5, 8), "10:00", "10:45", "temple", None, "Hindi", 10100, 0),
        ("bk_seed_5", "mem_vikram", "svc_archana", "pr_dube", nxt(1, 1), "08:00", "08:15", "temple", None, "Hindi", 2500, 0),
    ]
    for b in seeded:
        conn.execute(
            """INSERT INTO bookings (id, request_id, member_id, service_id, priest_id, date, start_time, end_time,
               location_type, city, language, base_price_cents, travel_fee_cents, total_cents, status, payment,
               approved_by, created_at) VALUES (?,NULL,?,?,?,?,?,?,?,?,?,?,?,?, 'confirmed', 'unpaid', 'seed data', ?)""",
            (*b, b[10] + b[11], created),
        )
    audit(conn, "system", "database_seeded", details={"seeded_on": seed_day.isoformat()})
    conn.execute("COMMIT")


MIGRATIONS = {
    "service_requests": {"risk_flags": "TEXT"},
    "agent_runs": {"provider": "TEXT", "portkey_target": "TEXT", "portkey_cache": "TEXT",
                   "portkey_cache_hits": "INTEGER", "http_log": "TEXT"},
}


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after a database was first created."""
    for table, cols in MIGRATIONS.items():
        have = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        for col, typ in cols.items():
            if col not in have:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")


def init_db(reset: bool = False) -> None:
    if reset and DB_PATH.exists():
        for suffix in ("", "-wal", "-shm"):
            p = DB_PATH.with_name(DB_PATH.name + suffix)
            if p.exists():
                p.unlink()
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        _migrate(conn)
        if conn.execute("SELECT COUNT(*) FROM services").fetchone()[0] == 0:
            seed(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    init_db(reset="--reset" in sys.argv)
    print(f"Database ready at {DB_PATH}")
