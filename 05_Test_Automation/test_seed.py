"""Tests for the demo-data loader (app/seed.py)."""
from app import seed
from app.db import get_conn


def _names():
    with get_conn() as c:
        return [r["full_name"] for r in c.execute("SELECT full_name FROM users WHERE role='CUSTOMER' ORDER BY id")]


def test_TC_A61_seed_loads_six_customers_including_team_members(client):
    seed.main()
    names = _names()
    assert len(names) == 6
    assert "S Anandita Narayan" in names and "Vivan Raj Belur" in names
    with get_conn() as c:
        assert c.execute("SELECT COUNT(*) n FROM bills").fetchone()["n"] == 18
        statuses = {r["status"] for r in c.execute("SELECT status FROM bills")}
        assert {"PAID", "UNPAID"} <= statuses                      # a realistic mix
        assert c.execute("SELECT COUNT(*) n FROM alerts").fetchone()["n"] == 1   # Karthik's spike


def test_TC_A62_seed_is_idempotent_and_customers_can_sign_in(client):
    seed.main()
    seed.main()                                                     # second run must change nothing
    assert len(_names()) == 6
    with get_conn() as c:
        assert c.execute("SELECT COUNT(*) n FROM complaints").fetchone()["n"] == 4
        assert {r["status"] for r in c.execute("SELECT status FROM complaints")} == {"OPEN", "IN_PROGRESS", "RESOLVED"}
        assert c.execute("SELECT COUNT(*) n FROM payments").fetchone()["n"] > 0      # paid bills have receipts
    r = client.post("/api/auth/login", json={"username": "anandita", "password": seed.PASSWORD})
    assert r.status_code == 200 and r.json()["full_name"] == "S Anandita Narayan"
