"""White/black-box unit tests of app/billing.py (techniques: BVA, equivalence partitioning,
decision table, state transition). Each test id maps to 02_Test_Case_Design / 03_Test_Execution."""
from datetime import date

import pytest

from app import billing as b


# ---- Boundary value analysis on tariff slabs (TC-U01 .. TC-U12) ----
@pytest.mark.parametrize("tc,units,expected", [
    ("TC-U01", 0, 0.0),
    ("TC-U02", 0.01, 0.05),
    ("TC-U03", 1, 5.0),
    ("TC-U04", 10, 50.0),
    ("TC-U05", 10.01, 50.08),
    ("TC-U06", 20, 130.0),
    ("TC-U07", 20.01, 130.12),
    ("TC-U08", 30, 250.0),
    ("TC-U09", 30.01, 250.2),
    ("TC-U10", 50, 650.0),
])
def test_domestic_water_charge_boundaries(tc, units, expected):
    assert b.water_charge(units, "DOMESTIC") == pytest.approx(expected, abs=0.005)


def test_TC_U11_negative_units_rejected():
    with pytest.raises(ValueError):
        b.water_charge(-0.01)


def test_TC_U12_invalid_connection_type_rejected():
    with pytest.raises(ValueError):
        b.water_charge(10, "INDUSTRIAL")


# ---- Equivalence partitioning on connection type (TC-U13 .. TC-U15) ----
def test_TC_U13_commercial_is_1_5x_domestic():
    assert b.water_charge(20, "COMMERCIAL") == pytest.approx(b.water_charge(20, "DOMESTIC") * 1.5)


def test_TC_U14_fixed_charges():
    assert b.bill_total(0, "DOMESTIC")["total"] == 50.0
    assert b.bill_total(0, "COMMERCIAL")["total"] == 150.0


def test_TC_U15_total_is_water_plus_fixed():
    r = b.bill_total(25, "DOMESTIC")
    assert r == {"water_charge": 190.0, "fixed_charge": 50.0, "total": 240.0}


# ---- Late fee boundary (TC-U16 .. TC-U18) ----
DUE = date(2026, 2, 16)


def test_TC_U16_no_fee_before_due_date():
    assert b.late_fee(240, DUE, date(2026, 2, 10)) == 0.0


def test_TC_U17_no_fee_on_due_date():
    assert b.late_fee(240, DUE, DUE) == 0.0


def test_TC_U18_fee_one_day_late():
    assert b.late_fee(240, DUE, date(2026, 2, 17)) == pytest.approx(25 + 4.8)


def test_TC_U19_due_date_is_15_days_after_bill_date():
    assert b.due_date_for(date(2026, 1, 20)) == date(2026, 2, 4)


# ---- Decision table: leak / high-usage alert (TC-U20 .. TC-U25) ----
@pytest.mark.parametrize("tc,units,prev,expected", [
    ("TC-U20", 50, [], False),                  # normal, no history
    ("TC-U21", 100, [], False),                 # at the absolute limit
    ("TC-U22", 100.01, [], True),               # just above the absolute limit
    ("TC-U23", 30, [10, 10], False),            # exactly 3x average -> not above
    ("TC-U24", 30.01, [10, 10], True),          # just above 3x average
    ("TC-U25", 5, [0, 0], False),               # zero average must not trigger
])
def test_leak_detection_decision_table(tc, units, prev, expected):
    assert b.is_leak_suspected(units, prev) is expected


# ---- State transition: bill lifecycle (TC-U26 .. TC-U30) ----
def test_TC_U26_unpaid_to_paid():
    assert b.next_status("UNPAID", "pay") == "PAID"


def test_TC_U27_unpaid_to_overdue():
    assert b.next_status("UNPAID", "due_passed") == "OVERDUE"


def test_TC_U28_overdue_to_paid():
    assert b.next_status("OVERDUE", "pay") == "PAID"


def test_TC_U29_paid_is_terminal():
    with pytest.raises(ValueError):
        b.next_status("PAID", "pay")


def test_TC_U30_paid_cannot_become_overdue():
    with pytest.raises(ValueError):
        b.next_status("PAID", "due_passed")
