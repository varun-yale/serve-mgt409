"""Deterministic tests: scheduling rules, approval gate, conflicts, admin auth.

No model calls. Each test gets a fresh seeded database in a temp directory.
Run: .venv/bin/python -m pytest tests -q
"""

from __future__ import annotations

import importlib
import json
from datetime import timedelta

import pytest


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("SERVE_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("SERVE_ADMIN_TOKEN", "test-admin-token")
    from backend import config
    importlib.reload(config)
    from backend import db, scheduling, pipeline, main
    for m in (db, scheduling, pipeline, main):
        importlib.reload(m)
    db.init_db(reset=True)
    from fastapi.testclient import TestClient
    client = TestClient(main.app)
    client.__enter__()
    yield {"db": db, "sch": scheduling, "pipeline": pipeline, "client": client}
    client.__exit__(None, None, None)


def next_weekday(db, wd: int, after: int = 1) -> str:
    d = db.today() + timedelta(days=after)
    return (d + timedelta(days=(wd - d.weekday()) % 7)).isoformat()


ADMIN = {"X-Admin-Token": "test-admin-token"}


def test_valid_home_slot_has_price_and_evidence(env):
    db, sch = env["db"], env["sch"]
    conn = db.connect()
    sat = next_weekday(db, 5, after=8)
    c = sch.check_slot(conn, service_id="svc_satyanarayan", priest_id="pr_joshi", date_str=sat,
                       start_time="14:00", location_type="home", city="Milford", language="Gujarati")
    assert c["ok"], c["problems"]
    assert c["total_cents"] == 15100 and c["travel_fee_cents"] == 0
    assert any("speaks Gujarati" in e for e in c["evidence"])


def test_rules_reject_language_travel_and_qualification(env):
    db, sch = env["db"], env["sch"]
    conn = db.connect()
    sat = next_weekday(db, 5, after=8)
    lang = sch.check_slot(conn, service_id="svc_satyanarayan", priest_id="pr_joshi", date_str=sat,
                          start_time="14:00", location_type="home", city="Milford", language="Tamil")
    assert not lang["ok"] and any("does not speak Tamil" in p for p in lang["problems"])
    far = sch.check_slot(conn, service_id="svc_griha", priest_id="pr_joshi", date_str=sat,
                         start_time="11:00", location_type="home", city="Hartford")
    assert not far["ok"] and any("travels at most" in p for p in far["problems"])
    unq = sch.check_slot(conn, service_id="svc_griha", priest_id="pr_dube", date_str=sat,
                         start_time="09:00", location_type="home", city="Hamden")
    assert not unq["ok"] and any("not qualified" in p for p in unq["problems"])


def test_conflict_with_seeded_booking_and_temple_event(env):
    db, sch = env["db"], env["sch"]
    conn = db.connect()
    sat = next_weekday(db, 5, after=1)  # bk_seed_1: Sharma 11:00-11:30 this Saturday
    c = sch.check_slot(conn, service_id="svc_abhishekam", priest_id="pr_sharma", date_str=sat,
                       start_time="11:00", location_type="temple")
    assert not c["ok"] and any("Conflicts with booking bk_seed_1" in p for p in c["problems"])
    diwali = conn.execute("SELECT date FROM events WHERE id = 'evt_diwali'").fetchone()[0]
    e = sch.check_slot(conn, service_id="svc_archana", priest_id="pr_sharma", date_str=diwali,
                       start_time="18:00", location_type="temple")
    assert not e["ok"] and any("Diwali" in p for p in e["problems"])


def test_time_off_blocks_priest(env):
    db, sch = env["db"], env["sch"]
    conn = db.connect()
    off = conn.execute("SELECT start_date FROM priest_time_off WHERE priest_id = 'pr_iyer'").fetchone()[0]
    c = sch.check_slot(conn, service_id="svc_archana", priest_id="pr_iyer", date_str=off,
                       start_time="08:00", location_type="temple")
    assert not c["ok"] and any("away" in p for p in c["problems"])


def _slot_request(env, date, time="08:00", service="svc_archana"):
    r = env["client"].post("/api/requests/slot", json={"service_id": service, "date": date, "start_time": time})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_admin_routes_require_token(env):
    c = env["client"]
    assert c.get("/api/admin/requests").status_code == 401
    assert c.get("/api/admin/requests", headers={"X-Admin-Token": "wrong"}).status_code == 401
    assert c.get("/api/admin/requests", headers=ADMIN).status_code == 200
    rid = _slot_request(env, next_weekday(env["db"], 3, after=2))
    r = c.post(f"/api/admin/requests/{rid}/approve", json={"admin_name": "Mallory", "option_index": 0})
    assert r.status_code == 401


def test_approve_persists_and_blocks_duplicate_and_overlap(env):
    c, db = env["client"], env["db"]
    thu = next_weekday(db, 3, after=2)
    r1 = _slot_request(env, thu)
    r2 = _slot_request(env, thu)  # same time; rules engine may pick the same first free priest
    ok = c.post(f"/api/admin/requests/{r1}/approve", json={"admin_name": "Meena", "option_index": 0}, headers=ADMIN)
    assert ok.status_code == 200, ok.text
    bid = ok.json()["booking_id"]

    # duplicate approval of the same request
    dup = c.post(f"/api/admin/requests/{r1}/approve", json={"admin_name": "Meena", "option_index": 0}, headers=ADMIN)
    assert dup.status_code == 409

    # second request recommended the same priest/time -> rechecked at approval and blocked
    detail = c.get(f"/api/admin/requests/{r2}", headers=ADMIN).json()
    same = detail["recommendation"]["options"][0]["priest_id"] == ok.json()["check"]["priest_id"]
    clash = c.post(f"/api/admin/requests/{r2}/approve", json={"admin_name": "Meena", "option_index": 0}, headers=ADMIN)
    if same:
        assert clash.status_code == 409 and any("Conflicts" in p for p in clash.json()["problems"])

    conn = db.connect()
    row = conn.execute("SELECT status FROM bookings WHERE id = ?", (bid,)).fetchone()
    assert row["status"] == "confirmed"
    assert conn.execute("SELECT status FROM service_requests WHERE id = ?", (r1,)).fetchone()[0] == "approved"
    actions = [a[0] for a in conn.execute("SELECT action FROM audit_events WHERE request_id = ?", (r1,))]
    assert "booking_approved" in actions


def test_edit_and_approve_rechecks_rules(env):
    c, db = env["client"], env["db"]
    thu = next_weekday(db, 3, after=2)
    rid = _slot_request(env, thu)
    bad = {"priest_id": "pr_dube", "date": next_weekday(db, 0, after=2), "start_time": "08:00", "location_type": "temple"}
    r = c.post(f"/api/admin/requests/{rid}/approve", json={"admin_name": "Meena", "slot": bad}, headers=ADMIN)
    assert r.status_code == 409  # Dube does not work Mondays
    good = {**bad, "date": thu, "priest_id": "pr_iyer"}
    r = c.post(f"/api/admin/requests/{rid}/approve", json={"admin_name": "Meena", "slot": good}, headers=ADMIN)
    assert r.status_code == 200, r.text
    conn = db.connect()
    assert conn.execute("SELECT decision FROM approvals WHERE request_id = ? ORDER BY id DESC", (rid,)).fetchone()[0] == "approved_edited"


def test_reject_and_cancel_free_the_slot(env):
    c, db = env["client"], env["db"]
    thu = next_weekday(db, 3, after=2)
    r1 = _slot_request(env, thu, "18:00")
    assert c.post(f"/api/admin/requests/{r1}/reject", json={"admin_name": "Meena", "message": "Hall closed"}, headers=ADMIN).status_code == 200
    assert c.post(f"/api/admin/requests/{r1}/approve", json={"admin_name": "Meena", "option_index": 0}, headers=ADMIN).status_code == 409
    r2 = _slot_request(env, thu, "18:00")
    bid = c.post(f"/api/admin/requests/{r2}/approve", json={"admin_name": "Meena", "option_index": 0}, headers=ADMIN).json()["booking_id"]
    assert c.post(f"/api/admin/bookings/{bid}/cancel", json={"admin_name": "Meena", "reason": "Family request"}, headers=ADMIN).status_code == 200
    me = c.get(f"/api/requests/{r2}").json()
    assert me["status"] == "cancelled"


def test_member_input_validation(env):
    c = env["client"]
    assert c.post("/api/requests", json={"text": "hi"}).status_code == 422
    assert c.post("/api/requests", json={"text": "x" * 1501}).status_code == 422
    assert c.post("/api/requests/slot", json={"service_id": "svc_archana", "date": "tomorrow", "start_time": "8"}).status_code == 422


def test_portal_bootstrap_shapes(env):
    p = env["client"].get("/api/portal").json()
    assert p["member"]["id"] == "mem_arjun_patel"
    assert any(s["id"] == "svc_archana" and s["slots"] for s in p["services"])
    assert all(e["isoDate"] >= p["today"] for e in p["events"])
    assert "PORTKEY" not in json.dumps(p)
