"""Payment history and receipts (TC-A63 .. TC-A72)."""
import pytest

from conftest import _login


def pay(client, headers, bill_id, amount, paid_on="2026-02-10", method=None):
    body = {"amount": amount, "paid_on": paid_on}
    if method:
        body["method"] = method
    return client.post(f"/api/bills/{bill_id}/pay", headers=headers, json=body)


def second_customer(client):
    client.post("/api/auth/register", json={"username": "carol", "password": "secret1", "full_name": "Carol"})
    return _login(client, "carol", "secret1")


def test_TC_A63_payment_creates_record_with_receipt_number(client, customer, bill):
    pay(client, customer[1], bill["id"], 240, method="CARD")
    payments = client.get("/api/payments", headers=customer[1]).json()
    assert len(payments) == 1
    p = payments[0]
    assert p["receipt_no"] == "RCP-000001" and p["bill_id"] == bill["id"]
    assert p["amount"] == 240 and p["method"] == "CARD" and p["paid_on"] == "2026-02-10"


def test_TC_A64_customer_sees_only_own_payments(client, customer, bill):
    pay(client, customer[1], bill["id"], 240)
    assert client.get("/api/payments", headers=second_customer(client)).json() == []


def test_TC_A65_admin_sees_all_payments_with_customer_name(client, admin, customer, bill):
    pay(client, customer[1], bill["id"], 240)
    rows = client.get("/api/payments", headers=admin).json()
    assert len(rows) == 1 and rows[0]["customer_name"] == "Alice" and rows[0]["meter_no"] == "MTR001"


def test_TC_A66_receipt_shows_full_breakdown(client, customer, bill):
    pay(client, customer[1], bill["id"], 240)
    pid = client.get("/api/payments", headers=customer[1]).json()[0]["id"]
    r = client.get(f"/api/payments/{pid}", headers=customer[1]).json()
    assert (r["water_charge"], r["fixed_charge"], r["bill_total"], r["late_fee"], r["amount"]) == (190, 50, 240, 0, 240)
    assert r["units"] == 25 and r["customer_name"] == "Alice" and r["address"] == "12 Lake Road"


def test_TC_A67_cannot_view_someone_elses_receipt(client, customer, bill):
    pay(client, customer[1], bill["id"], 240)
    pid = client.get("/api/payments", headers=customer[1]).json()[0]["id"]
    assert client.get(f"/api/payments/{pid}", headers=second_customer(client)).status_code == 403


def test_TC_A68_unknown_receipt(client, admin):
    assert client.get("/api/payments/9999", headers=admin).status_code == 404


def test_TC_A69_invalid_payment_method_rejected(client, customer, bill):
    assert pay(client, customer[1], bill["id"], 240, method="BITCOIN").status_code == 422
    assert client.get("/api/payments", headers=customer[1]).json() == []


def test_TC_A70_payment_history_requires_login(client):
    assert client.get("/api/payments").status_code == 401


def test_TC_A71_late_payment_record_includes_late_fee(client, customer, bill):
    pay(client, customer[1], bill["id"], 269.8, paid_on="2026-02-17")
    p = client.get("/api/payments", headers=customer[1]).json()[0]
    assert p["late_fee"] == 29.8 and p["amount"] == 269.8


def test_TC_A72_rejected_or_repeated_payment_creates_no_extra_record(client, customer, bill):
    pay(client, customer[1], bill["id"], 100)                    # wrong amount, rejected
    pay(client, customer[1], bill["id"], 240)                    # ok
    pay(client, customer[1], bill["id"], 240)                    # already paid, rejected
    assert len(client.get("/api/payments", headers=customer[1]).json()) == 1


@pytest.mark.parametrize("tc,method", [("TC-A109", "UPI"), ("TC-A110", "CARD"), ("TC-A111", "NETBANKING"), ("TC-A112", "CASH")])
def test_every_supported_payment_method_is_accepted(client, customer, bill, tc, method):
    assert pay(client, customer[1], bill["id"], 240, method=method).status_code == 200
