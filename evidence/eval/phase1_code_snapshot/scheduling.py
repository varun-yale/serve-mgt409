"""Deterministic scheduling rules and read-only data lookups.

Everything here reads SQLite and applies fixed business rules. The agents call
these functions as tools, and the approval route calls `check_slot` again inside
a transaction — so the model can suggest, but never decide, whether a slot is
valid.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta

from .db import today

LANG_ANY = {"", "any", "none", "no preference", "either", "not specified"}


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def to_min(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def to_hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def norm_city(city: str | None) -> str | None:
    if not city:
        return None
    c = city.strip().lower()
    for suffix in (", connecticut", ", ct", " ct", ", ct."):
        if c.endswith(suffix):
            c = c[: -len(suffix)]
    return c.strip() or None


def norm_lang(lang: str | None) -> str | None:
    if lang is None or lang.strip().lower() in LANG_ANY:
        return None
    return lang.strip().capitalize()


def parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def policies(conn: sqlite3.Connection) -> dict[str, str]:
    return {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM policies")}


def _service(conn, service_id):
    return conn.execute("SELECT * FROM services WHERE id = ?", (service_id,)).fetchone()


def _priest(conn, priest_id):
    return conn.execute("SELECT * FROM priests WHERE id = ?", (priest_id,)).fetchone()


def _languages(conn, priest_id) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT language FROM priest_languages WHERE priest_id = ? ORDER BY language", (priest_id,))]


def _zone(conn, city):
    c = norm_city(city)
    return conn.execute("SELECT * FROM travel_zones WHERE city = ?", (c,)).fetchone() if c else None


def travel_fee_cents(conn, miles: int) -> int:
    p = policies(conn)
    extra = max(0, miles - int(p["included_travel_miles"]))
    return extra * int(p["travel_fee_per_mile_cents"])


# ---------------------------------------------------------------------------
# the rule check used by tools AND by the approval route
# ---------------------------------------------------------------------------

def check_slot(conn: sqlite3.Connection, *, service_id: str, priest_id: str, date_str: str,
               start_time: str, location_type: str, city: str | None = None,
               language: str | None = None, exclude_booking_id: str | None = None) -> dict:
    """Apply every scheduling rule to one proposed slot.

    Returns ok, a list of problems (any problem means the slot is invalid),
    warnings, the evidence that passed, and the price computed from the database.
    """
    problems: list[str] = []
    warnings: list[str] = []
    evidence: list[str] = []
    p = policies(conn)

    svc = _service(conn, service_id)
    if not svc or not svc["enabled"]:
        return {"ok": False, "problems": [f"Service '{service_id}' does not exist or is not offered."],
                "warnings": [], "evidence": []}
    pr = _priest(conn, priest_id)
    if not pr or not pr["active"]:
        return {"ok": False, "problems": [f"Priest '{priest_id}' does not exist or is inactive."],
                "warnings": [], "evidence": []}

    d = parse_date(date_str)
    try:
        start = to_min(start_time)
    except (ValueError, AttributeError):
        start = None
    if d is None or start is None:
        return {"ok": False, "problems": ["Date must be YYYY-MM-DD and time HH:MM."], "warnings": [], "evidence": []}

    duration = svc["duration_minutes"]
    end = start + duration
    loc = location_type if location_type in ("temple", "home") else None
    if loc is None:
        problems.append("Location must be 'temple' or 'home'.")
    elif svc["location_mode"] != "either" and svc["location_mode"] != loc:
        problems.append(f"{svc['name']} is only performed at the {svc['location_mode']}.")
    else:
        evidence.append(f"{svc['name']} can be performed at the {loc}.")

    # qualification and language
    qualified = conn.execute("SELECT 1 FROM priest_qualifications WHERE priest_id = ? AND service_id = ?",
                             (priest_id, service_id)).fetchone()
    if qualified:
        evidence.append(f"{pr['name']} is qualified to perform {svc['name']}.")
    else:
        problems.append(f"{pr['name']} is not qualified to perform {svc['name']}.")
    lang = norm_lang(language)
    langs = _languages(conn, priest_id)
    if lang:
        if lang.lower() in (x.lower() for x in langs):
            evidence.append(f"{pr['name']} speaks {lang}.")
        else:
            problems.append(f"{pr['name']} does not speak {lang} (speaks {', '.join(langs)}).")

    # lead time and booking horizon
    days_ahead = (d - today()).days
    if days_ahead < 0:
        problems.append(f"{date_str} is in the past.")
    elif days_ahead < svc["min_lead_days"]:
        problems.append(f"{svc['name']} needs at least {svc['min_lead_days']} days' notice; {date_str} is {days_ahead} days away.")
    elif days_ahead > int(p["max_advance_days"]):
        problems.append(f"Bookings open at most {p['max_advance_days']} days ahead.")
    else:
        evidence.append(f"{date_str} is {days_ahead} days away, within the booking window.")
        if svc["recommended_lead_days"] and days_ahead < svc["recommended_lead_days"]:
            warnings.append(f"Shorter notice than the recommended {svc['recommended_lead_days']} days for {svc['name']}.")

    if svc["scheduling"] == "fixed_slots":
        slots = json.loads(svc["slot_times"] or "[]")
        if start_time not in slots:
            problems.append(f"{svc['name']} runs only at fixed times: {', '.join(slots)}.")

    # location, travel and pricing
    travel = 0
    fee = 0
    zone = None
    if loc == "home":
        zone = _zone(conn, city)
        if not city:
            problems.append("A home service needs the town or city of the home.")
        elif not zone:
            problems.append(f"'{city}' is not in the temple's service area table.")
        else:
            travel = zone["drive_minutes"]
            if zone["miles"] > int(p["max_service_radius_miles"]):
                problems.append(f"{zone['display_name']} is {zone['miles']} miles away, beyond the {p['max_service_radius_miles']}-mile service radius.")
            elif zone["miles"] > pr["max_travel_miles"]:
                problems.append(f"{zone['display_name']} is {zone['miles']} miles away; {pr['name']} travels at most {pr['max_travel_miles']} miles.")
            else:
                fee = travel_fee_cents(conn, zone["miles"])
                evidence.append(f"{zone['display_name']} is {zone['miles']} miles / {travel} min each way; travel fee ${fee / 100:.2f}.")
        if start < to_min(p["home_service_earliest"]) or end > to_min(p["home_service_latest_end"]):
            problems.append(f"Home services run between {p['home_service_earliest']} and {p['home_service_latest_end']}.")
    elif loc == "temple":
        if start < to_min(p["temple_open"]) or end > to_min(p["temple_close"]):
            problems.append(f"Temple services run between {p['temple_open']} and {p['temple_close']}.")

    busy_start, busy_end = start - travel, end + travel

    # weekly availability
    windows = conn.execute("SELECT start_time, end_time FROM priest_availability WHERE priest_id = ? AND weekday = ?",
                           (priest_id, d.weekday())).fetchall()
    fits = [w for w in windows if to_min(w["start_time"]) <= busy_start and busy_end <= to_min(w["end_time"])]
    if fits:
        evidence.append(f"Inside {pr['name']}'s {d.strftime('%A')} hours {fits[0]['start_time']}–{fits[0]['end_time']}"
                        + (" including travel." if travel else "."))
    elif windows:
        hours = ", ".join(f"{w['start_time']}–{w['end_time']}" for w in windows)
        problems.append(f"{to_hhmm(busy_start)}–{to_hhmm(busy_end)} is outside {pr['name']}'s {d.strftime('%A')} hours ({hours}).")
    else:
        problems.append(f"{pr['name']} does not work on {d.strftime('%A')}s.")

    # time off
    off = conn.execute("SELECT * FROM priest_time_off WHERE priest_id = ? AND start_date <= ? AND end_date >= ?",
                       (priest_id, date_str, date_str)).fetchone()
    if off:
        problems.append(f"{pr['name']} is away {off['start_date']} to {off['end_date']} ({off['reason']}).")

    # conflicts with confirmed bookings (with travel and buffer)
    buffer = int(p["buffer_minutes"])
    rows = conn.execute(
        "SELECT b.*, s.name AS service_name FROM bookings b JOIN services s ON s.id = b.service_id "
        "WHERE b.priest_id = ? AND b.date = ? AND b.status = 'confirmed' AND (? IS NULL OR b.id != ?)",
        (priest_id, date_str, exclude_booking_id, exclude_booking_id)).fetchall()
    clash = False
    for b in rows:
        bz = _zone(conn, b["city"]) if b["location_type"] == "home" else None
        bt = bz["drive_minutes"] if bz else 0
        b_start, b_end = to_min(b["start_time"]) - bt, to_min(b["end_time"]) + bt
        if busy_start < b_end + buffer and b_start < busy_end + buffer:
            clash = True
            problems.append(f"Conflicts with booking {b['id']} ({b['service_name']} {b['start_time']}–{b['end_time']}"
                            + (f" at a home in {bz['display_name']}" if bz else "") + f"; {buffer}-min buffer required).")
    # conflicts with temple events that occupy priests
    events = conn.execute(
        "SELECT * FROM events WHERE date = ? AND (blocks_all_priests = 1 OR blocked_priest_id = ?)",
        (date_str, priest_id)).fetchall()
    for e in events:
        if busy_start < to_min(e["end_time"]) + buffer and to_min(e["start_time"]) < busy_end + buffer:
            clash = True
            problems.append(f"Conflicts with temple event '{e['name']}' {e['start_time']}–{e['end_time']}.")
    if not clash:
        evidence.append(f"No conflicting bookings or temple events for {pr['name']} on {date_str}.")

    return {
        "ok": not problems,
        "problems": problems,
        "warnings": warnings,
        "evidence": evidence,
        "service_id": service_id,
        "service_name": svc["name"],
        "priest_id": priest_id,
        "priest_name": pr["name"],
        "date": date_str,
        "start_time": start_time,
        "end_time": to_hhmm(end),
        "location_type": loc,
        "city": zone["display_name"] if zone else None,
        "language": lang,
        "base_price_cents": svc["price_cents"],
        "travel_fee_cents": fee,
        "total_cents": svc["price_cents"] + fee,
    }


# ---------------------------------------------------------------------------
# read-only lookups exposed as agent tools
# ---------------------------------------------------------------------------

def list_services(conn) -> list[dict]:
    return [
        {"service_id": r["id"], "name": r["name"], "also_called": json.loads(r["aliases"]),
         "where": r["location_mode"], "scheduling": r["scheduling"], "price": r["price_label"],
         "duration_minutes": r["duration_minutes"]}
        for r in conn.execute("SELECT * FROM services WHERE enabled = 1 ORDER BY name")
    ]


def get_service_details(conn, service_id: str) -> dict:
    r = _service(conn, service_id)
    if not r:
        return {"error": f"No service with id '{service_id}'."}
    return {
        "service_id": r["id"], "name": r["name"], "price_cents": r["price_cents"], "price_label": r["price_label"],
        "duration_minutes": r["duration_minutes"], "scheduling": r["scheduling"],
        "location_mode": r["location_mode"], "temple_room": r["temple_room"],
        "fixed_start_times": json.loads(r["slot_times"]) if r["slot_times"] else None,
        "min_lead_days": r["min_lead_days"], "recommended_lead_days": r["recommended_lead_days"],
        "enabled": bool(r["enabled"]),
    }


def find_qualified_priests(conn, service_id: str, language: str | None = None) -> list[dict]:
    lang = norm_lang(language)
    out = []
    for r in conn.execute(
        "SELECT p.* FROM priests p JOIN priest_qualifications q ON q.priest_id = p.id "
        "WHERE q.service_id = ? AND p.active = 1 ORDER BY p.name", (service_id,)):
        langs = _languages(conn, r["id"])
        out.append({
            "priest_id": r["id"], "name": r["name"], "title": r["title"], "languages": langs,
            "speaks_requested_language": None if not lang else lang.lower() in (x.lower() for x in langs),
            "max_travel_miles": r["max_travel_miles"],
        })
    return out


def get_travel_info(conn, city: str) -> dict:
    z = _zone(conn, city)
    p = policies(conn)
    if not z:
        return {"city": city, "in_service_area_table": False,
                "note": "Town not in the temple's service-area table; staff must confirm travel manually."}
    return {"city": z["display_name"], "in_service_area_table": True, "miles_one_way": z["miles"],
            "drive_minutes_one_way": z["drive_minutes"], "travel_fee_cents": travel_fee_cents(conn, z["miles"]),
            "within_service_radius": z["miles"] <= int(p["max_service_radius_miles"])}


def get_priest_day(conn, priest_id: str, date_str: str) -> dict:
    pr = _priest(conn, priest_id)
    d = parse_date(date_str)
    if not pr or not d:
        return {"error": "Unknown priest or bad date (use YYYY-MM-DD)."}
    windows = conn.execute("SELECT start_time, end_time FROM priest_availability WHERE priest_id = ? AND weekday = ?",
                           (priest_id, d.weekday())).fetchall()
    off = conn.execute("SELECT start_date, end_date, reason FROM priest_time_off WHERE priest_id = ? AND start_date <= ? AND end_date >= ?",
                       (priest_id, date_str, date_str)).fetchone()
    bookings = conn.execute(
        "SELECT b.start_time, b.end_time, b.location_type, b.city, s.name AS service FROM bookings b "
        "JOIN services s ON s.id = b.service_id WHERE b.priest_id = ? AND b.date = ? AND b.status = 'confirmed' "
        "ORDER BY b.start_time", (priest_id, date_str)).fetchall()
    events = conn.execute(
        "SELECT name, start_time, end_time FROM events WHERE date = ? AND (blocks_all_priests = 1 OR blocked_priest_id = ?)",
        (date_str, priest_id)).fetchall()
    return {
        "priest": pr["name"], "date": date_str, "weekday": d.strftime("%A"),
        "working_hours": [f"{w['start_time']}–{w['end_time']}" for w in windows],
        "time_off": dict(off) if off else None,
        "confirmed_bookings": [dict(b) for b in bookings],
        "temple_events_blocking": [dict(e) for e in events],
    }


def get_scheduling_policies(conn) -> dict:
    return {r["key"]: {"value": r["value"], "meaning": r["description"]}
            for r in conn.execute("SELECT * FROM policies")}


def get_member_profile(conn, member_id: str) -> dict:
    r = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if not r:
        return {"error": "Unknown member."}
    z = _zone(conn, r["home_city"])
    return {"name": r["name"], "home_city_on_file": z["display_name"] if z else r["home_city"]}


def _time_ok(start: int, time_of_day: str | None) -> bool:
    if time_of_day == "morning":
        return start < 12 * 60
    if time_of_day == "afternoon":
        return 12 * 60 <= start < 17 * 60
    if time_of_day == "evening":
        return start >= 17 * 60
    return True


def search_available_slots(conn, *, service_id: str, date_str: str, location_type: str,
                           city: str | None = None, language: str | None = None,
                           time_of_day: str | None = None, priest_id: str | None = None,
                           limit: int = 6, per_priest: int = 2) -> dict:
    """Every slot on one date that passes `check_slot`, across qualified priests,
    plus the main reason each excluded priest had nothing."""
    svc = _service(conn, service_id)
    if not svc:
        return {"error": f"No service with id '{service_id}'."}
    if parse_date(date_str) is None:
        return {"error": "Date must be YYYY-MM-DD."}
    candidates = (json.loads(svc["slot_times"]) if svc["scheduling"] == "fixed_slots"
                  else [to_hhmm(m) for m in range(6 * 60 + 30, 20 * 60 + 1, 30)])
    priests = [x for x in find_qualified_priests(conn, service_id) if not priest_id or x["priest_id"] == priest_id]
    found, excluded = [], {}
    for pr in priests:
        reasons: dict[str, int] = {}
        hits = 0
        for t in candidates:
            if not _time_ok(to_min(t), time_of_day):
                continue
            c = check_slot(conn, service_id=service_id, priest_id=pr["priest_id"], date_str=date_str,
                           start_time=t, location_type=location_type, city=city, language=language)
            if c["ok"]:
                hits += 1
                found.append({k: c[k] for k in ("priest_id", "priest_name", "date", "start_time", "end_time",
                                                "location_type", "city", "base_price_cents", "travel_fee_cents",
                                                "total_cents", "warnings")})
            else:
                for prob in c["problems"]:
                    key = prob.split(" (")[0] if "outside" in prob else prob
                    reasons[key] = reasons.get(key, 0) + 1
        if not hits:
            excluded[pr["name"]] = sorted(reasons, key=reasons.get, reverse=True)[:2] or ["No candidate times in that part of the day."]
    # Spread suggestions across priests rather than listing one priest's every half hour.
    found.sort(key=lambda s: (s["start_time"], s["priest_name"]))
    picked, per_priest_count = [], {}
    for s in found:
        if per_priest_count.get(s["priest_id"], 0) < per_priest:
            picked.append(s)
            per_priest_count[s["priest_id"]] = per_priest_count.get(s["priest_id"], 0) + 1
        if len(picked) >= limit:
            break
    return {"service": svc["name"], "date": date_str, "open_slots_found": len(found), "slots": picked,
            "priests_with_no_slot": excluded}


def fixed_slot_calendar(conn, service_id: str, days: int = 7, max_dates: int = 4) -> list[dict]:
    """Upcoming dates/times with at least one qualified, free priest (member slot picker)."""
    svc = _service(conn, service_id)
    if not svc or svc["scheduling"] != "fixed_slots":
        return []
    out = []
    start = today() + timedelta(days=max(1, svc["min_lead_days"]))
    for i in range(days + 7):
        d = (start + timedelta(days=i)).isoformat()
        res = search_available_slots(conn, service_id=service_id, date_str=d, location_type="temple", limit=200, per_priest=200)
        times = sorted({s["start_time"] for s in res.get("slots", [])})
        if times:
            out.append({"date": d, "times": times})
        if len(out) >= max_dates:
            break
    return out


def first_free_priest(conn, *, service_id: str, date_str: str, start_time: str) -> dict | None:
    """For the slot picker: the first qualified priest for whom the slot passes every rule."""
    for pr in find_qualified_priests(conn, service_id):
        c = check_slot(conn, service_id=service_id, priest_id=pr["priest_id"], date_str=date_str,
                       start_time=start_time, location_type="temple")
        if c["ok"]:
            return c
    return None
