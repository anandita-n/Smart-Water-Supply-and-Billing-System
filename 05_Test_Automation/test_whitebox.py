"""White-box tests (TC-W01 onwards).

These tests are designed from the CODE, not from the requirements:
  * Basis path testing: for each function the cyclomatic complexity V(G) was worked out from its
    control-flow graph, and one test was written per independent path.
  * Branch coverage: the coverage report was run with --cov-branch and a test was written for every
    branch that no black-box test had reached (the remaining decisions in main.py and db.py).
See 02_Test_Case_Design/Test_Case_Design.md, section 14, for the graphs and the path tables.
"""
import sqlite3
from datetime import date

import pytest

from app import billing, complaints
from app.db import get_conn, init_db


# ---------------------------------------------------------------------------
# water_charge()   V(G) = 7   (decisions: units<0, bad type, loop, remaining<=0, width is None, COMMERCIAL)
# ---------------------------------------------------------------------------
def test_TC_W01_path_negative_units_raises():                        # path 1: units < 0 true
    with pytest.raises(ValueError):
        billing.water_charge(-1)


def test_TC_W02_path_invalid_type_raises():                          # path 2: units ok, type not in table
    with pytest.raises(ValueError):
        billing.water_charge(5, "INDUSTRIAL")


def test_TC_W03_path_zero_units_leaves_the_loop_at_once():           # path 3: loop breaks on its first pass
    assert billing.water_charge(0) == 0.0


def test_TC_W04_path_usage_inside_first_slab():                      # path 4: one slab used, break on 2nd pass
    assert billing.water_charge(5) == 25.0


def test_TC_W05_path_usage_ends_exactly_at_a_slab_edge():            # path 5: three slabs used, break on 4th pass
    assert billing.water_charge(30) == 250.0


def test_TC_W06_path_usage_reaches_the_open_ended_slab():            # path 6: width is None branch, loop ends normally
    assert billing.water_charge(50) == 650.0


def test_TC_W07_path_commercial_multiplier_applied():                # path 7: COMMERCIAL branch true
    assert billing.water_charge(20, "COMMERCIAL") == 195.0


# ---------------------------------------------------------------------------
# is_leak_suspected()   V(G) = 5   (units>100, previous_units, avg>0, units>3*avg)
# ---------------------------------------------------------------------------
def test_TC_W08_leak_path_high_usage_returns_true_early():
    assert billing.is_leak_suspected(150, []) is True


def test_TC_W09_leak_path_no_history_returns_false():
    assert billing.is_leak_suspected(50, []) is False


def test_TC_W10_leak_path_zero_average_skips_the_spike_check():
    assert billing.is_leak_suspected(5, [0, 0]) is False


def test_TC_W11_leak_path_history_present_but_no_spike():
    assert billing.is_leak_suspected(20, [10, 10]) is False


def test_TC_W12_leak_path_spike_over_three_times_average():
    assert billing.is_leak_suspected(31, [10, 10]) is True


# ---------------------------------------------------------------------------
# late_fee()  V(G) = 2,   next_status() (billing)  V(G) = 2,   complaints.*  V(G) = 2 / 3
# ---------------------------------------------------------------------------
def test_TC_W13_late_fee_path_on_time_returns_zero():
    assert billing.late_fee(240, date(2026, 2, 16), date(2026, 2, 16)) == 0.0


def test_TC_W14_late_fee_path_late_returns_flat_plus_percent():
    assert billing.late_fee(240, date(2026, 2, 16), date(2026, 2, 17)) == 29.80


def test_TC_W15_bill_state_path_valid_transition_found_in_table():
    assert billing.next_status("UNPAID", "pay") == "PAID"


def test_TC_W16_bill_state_path_missing_transition_raises():
    with pytest.raises(ValueError):
        billing.next_status("PAID", "pay")


def test_TC_W17_complaint_state_path_valid_then_invalid():
    assert complaints.next_status("OPEN", "IN_PROGRESS") == "IN_PROGRESS"
    with pytest.raises(ValueError):
        complaints.next_status("OPEN", "RESOLVED")


def test_TC_W18_allowed_next_loop_matches_and_skips_entries():
    assert complaints.allowed_next("OPEN") == ["IN_PROGRESS"]        # loop finds a match
    assert complaints.allowed_next("RESOLVED") == []                 # loop never matches


# ---------------------------------------------------------------------------
# Branch coverage of main.py / db.py: branches that no black-box test had reached
# ---------------------------------------------------------------------------
def test_TC_W19_admin_branch_of_list_connections(client, admin, connection):
    r = client.get("/api/connections", headers=admin)
    assert r.status_code == 200 and len(r.json()) == 1


def test_TC_W20_admin_branch_of_list_alerts(client, admin):
    r = client.get("/api/alerts", headers=admin)
    assert r.status_code == 200 and r.json() == []


def test_TC_W21_customer_cannot_read_another_customers_bill(client, admin, bill):
    client.post("/api/auth/register", json={"username": "mallory", "password": "secret1", "full_name": "Mallory"})
    token = client.post("/api/auth/login", json={"username": "mallory", "password": "secret1"}).json()["token"]
    r = client.get(f"/api/bills/{bill['id']}", headers={"Authorization": "Bearer " + token})
    assert r.status_code == 403


def test_TC_W22_complaint_about_an_unknown_connection_is_404(client, customer):
    _, hdr = customer
    r = client.post("/api/complaints", headers=hdr,
                    json={"category": "LEAK", "description": "Water leaking near the gate.", "connection_id": 9999})
    assert r.status_code == 404


def test_TC_W23_home_page_is_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "HydroCore" in r.text


def test_TC_W24_old_database_is_migrated_and_paid_bills_get_a_payment(tmp_path, monkeypatch):
    """init_db() must add the columns that older databases lack and back-fill payments."""
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript("""
        CREATE TABLE users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
                           password_hash TEXT NOT NULL, full_name TEXT NOT NULL, role TEXT NOT NULL);
        CREATE TABLE tokens(token TEXT PRIMARY KEY, user_id INTEGER NOT NULL);
        CREATE TABLE bills(id INTEGER PRIMARY KEY AUTOINCREMENT, connection_id INTEGER NOT NULL,
                           reading_id INTEGER UNIQUE NOT NULL, units REAL NOT NULL, water_charge REAL NOT NULL,
                           fixed_charge REAL NOT NULL, total REAL NOT NULL, bill_date TEXT NOT NULL,
                           due_date TEXT NOT NULL, status TEXT NOT NULL, late_fee REAL NOT NULL DEFAULT 0, paid_on TEXT);
        INSERT INTO bills(connection_id,reading_id,units,water_charge,fixed_charge,total,bill_date,due_date,status,paid_on)
        VALUES(1,1,25,190,50,240,'2026-01-01','2026-01-16','PAID','2026-01-05');
    """)
    old.commit()
    old.close()
    monkeypatch.setenv("WATER_DB", str(path))
    init_db()
    with get_conn() as c:
        tokens = [r["name"] for r in c.execute("PRAGMA table_info(tokens)")]
        users = [r["name"] for r in c.execute("PRAGMA table_info(users)")]
        pay = c.execute("SELECT amount, paid_on FROM payments").fetchall()
    assert "expires_at" in tokens
    assert "failed_attempts" in users and "locked_until" in users
    assert len(pay) == 1 and pay[0]["amount"] == 240 and pay[0]["paid_on"] == "2026-01-05"


def test_TC_W25_owner_and_admin_can_read_a_bill(client, admin, customer, bill):
    _, hdr = customer
    assert client.get(f"/api/bills/{bill['id']}", headers=hdr).json()["total"] == 240.0      # owner
    assert client.get(f"/api/bills/{bill['id']}", headers=admin).status_code == 200          # admin
    assert client.get("/api/bills/9999", headers=admin).status_code == 404                   # unknown id
