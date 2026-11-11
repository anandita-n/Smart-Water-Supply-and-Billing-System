"""API / integration tests (pytest + FastAPI TestClient). Ids map to 02_Test_Case_Design."""
import pytest

from conftest import add_reading


# ---------------- Authentication & registration ----------------
def test_TC_A01_register_valid_customer(client):
    r = client.post("/api/auth/register", json={"username": "bob_1", "password": "secret1", "full_name": "Bob"})
    assert r.status_code == 201 and r.json()["role"] == "CUSTOMER"


def test_TC_A02_register_duplicate_username(client):
    body = {"username": "bob", "password": "secret1", "full_name": "Bob"}
    client.post("/api/auth/register", json=body)
    assert client.post("/api/auth/register", json=body).status_code == 409


@pytest.mark.parametrize("tc,body", [
    ("TC-A03", {"username": "ab", "password": "secret1", "full_name": "X"}),          # username too short (min 3)
    ("TC-A04", {"username": "a" * 31, "password": "secret1", "full_name": "X"}),      # username too long (max 30)
    ("TC-A05", {"username": "bad name!", "password": "secret1", "full_name": "X"}),   # illegal characters
    ("TC-A06", {"username": "bobby", "password": "12345", "full_name": "X"}),         # password too short (min 6)
    ("TC-A07", {"username": "bobby", "password": "secret1", "full_name": ""}),        # empty name
])
def test_register_invalid_input(client, tc, body):
    assert client.post("/api/auth/register", json=body).status_code == 422


@pytest.mark.parametrize("tc,username,length", [("TC-A08", "abc", 3), ("TC-A09", "a" * 30, 30)])
def test_register_username_length_boundaries_accepted(client, tc, username, length):
    r = client.post("/api/auth/register", json={"username": username, "password": "secret1", "full_name": "X"})
    assert r.status_code == 201


def test_TC_A10_login_success_returns_token(client, customer):
    r = client.post("/api/auth/login", json={"username": "alice", "password": "secret1"})
    assert r.status_code == 200 and r.json()["token"] and r.json()["role"] == "CUSTOMER"


@pytest.mark.parametrize("tc,u,p", [("TC-A11", "alice", "wrong"), ("TC-A12", "nobody", "secret1")])
def test_login_failures(client, customer, tc, u, p):
    assert client.post("/api/auth/login", json={"username": u, "password": p}).status_code == 401


def test_TC_A13_protected_endpoint_requires_token(client):
    assert client.get("/api/bills").status_code == 401


def test_TC_A14_garbage_token_rejected(client):
    assert client.get("/api/me", headers={"Authorization": "Bearer nope"}).status_code == 401


# ---------------- Role-based access ----------------
def test_TC_A15_customer_cannot_create_connection(client, customer):
    cid, h = customer
    r = client.post("/api/connections", headers=h, json={
        "customer_id": cid, "meter_no": "MTRX", "type": "DOMESTIC", "address": "somewhere"})
    assert r.status_code == 403


def test_TC_A16_customer_cannot_add_reading(client, customer, connection):
    _, h = customer
    assert add_reading(client, h, connection, 10, "2026-01-01").status_code == 403


def test_TC_A17_customer_cannot_generate_bill(client, customer, connection):
    _, h = customer
    assert client.post("/api/bills/generate", headers=h, json={"connection_id": connection}).status_code == 403


# ---------------- Connections ----------------
def test_TC_A18_create_connection_ok(client, admin, customer):
    cid, _ = customer
    r = client.post("/api/connections", headers=admin, json={
        "customer_id": cid, "meter_no": "MTR100", "type": "COMMERCIAL", "address": "5 Market St"})
    assert r.status_code == 201


def test_TC_A19_duplicate_meter_number(client, admin, customer, connection):
    cid, _ = customer
    r = client.post("/api/connections", headers=admin, json={
        "customer_id": cid, "meter_no": "MTR001", "type": "DOMESTIC", "address": "another place"})
    assert r.status_code == 409


def test_TC_A20_connection_for_unknown_customer(client, admin):
    r = client.post("/api/connections", headers=admin, json={
        "customer_id": 9999, "meter_no": "MTR200", "type": "DOMESTIC", "address": "nowhere"})
    assert r.status_code == 404


def test_TC_A21_connection_invalid_type(client, admin, customer):
    cid, _ = customer
    r = client.post("/api/connections", headers=admin, json={
        "customer_id": cid, "meter_no": "MTR300", "type": "INDUSTRIAL", "address": "factory"})
    assert r.status_code == 422


def test_TC_A22_customer_sees_only_own_connections(client, admin, customer, connection):
    client.post("/api/auth/register", json={"username": "carol", "password": "secret1", "full_name": "Carol"})
    h2 = {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": "carol", "password": "secret1"}).json()["token"]}
    assert client.get("/api/connections", headers=h2).json() == []
    assert len(client.get("/api/connections", headers=customer[1]).json()) == 1


# ---------------- Meter readings ----------------
def test_TC_A23_first_reading_ok(client, admin, connection):
    assert add_reading(client, admin, connection, 100, "2026-01-01").status_code == 201


def test_TC_A24_reading_lower_than_previous_rejected(client, admin, connection):
    add_reading(client, admin, connection, 100, "2026-01-01")
    assert add_reading(client, admin, connection, 99.99, "2026-02-01").status_code == 400


def test_TC_A25_reading_equal_to_previous_accepted(client, admin, connection):
    add_reading(client, admin, connection, 100, "2026-01-01")
    assert add_reading(client, admin, connection, 100, "2026-02-01").status_code == 201


def test_TC_A26_negative_reading_rejected(client, admin, connection):
    assert add_reading(client, admin, connection, -1, "2026-01-01").status_code == 422


def test_TC_A27_reading_date_before_previous_rejected(client, admin, connection):
    add_reading(client, admin, connection, 100, "2026-02-01")
    assert add_reading(client, admin, connection, 110, "2026-01-01").status_code == 400


def test_TC_A28_reading_for_unknown_connection(client, admin):
    assert add_reading(client, admin, 9999, 10, "2026-01-01").status_code == 404


def test_TC_A29_future_dated_reading_rejected(client, admin, connection):
    assert add_reading(client, admin, connection, 100, "2999-01-01").status_code == 400


# ---------------- Bill generation ----------------
def test_TC_A30_bill_needs_two_readings(client, admin, connection):
    add_reading(client, admin, connection, 100, "2026-01-01")
    assert client.post("/api/bills/generate", headers=admin, json={"connection_id": connection}).status_code == 400


def test_TC_A31_bill_amounts_and_due_date(bill):
    assert bill["units"] == 25 and bill["water_charge"] == 190 and bill["fixed_charge"] == 50
    assert bill["total"] == 240 and bill["due_date"] == "2026-02-16" and bill["status"] == "UNPAID"


def test_TC_A32_duplicate_bill_for_same_reading_rejected(client, admin, connection, bill):
    assert client.post("/api/bills/generate", headers=admin, json={"connection_id": connection}).status_code == 409


def test_TC_A33_bill_unknown_connection(client, admin):
    assert client.post("/api/bills/generate", headers=admin, json={"connection_id": 9999}).status_code == 404


def test_TC_A34_customer_sees_own_bill_only(client, customer, bill):
    assert [b["id"] for b in client.get("/api/bills", headers=customer[1]).json()] == [bill["id"]]
    client.post("/api/auth/register", json={"username": "carol", "password": "secret1", "full_name": "Carol"})
    h2 = {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": "carol", "password": "secret1"}).json()["token"]}
    assert client.get("/api/bills", headers=h2).json() == []
    assert client.get(f"/api/bills/{bill['id']}", headers=h2).status_code == 403


def test_TC_A35_unpaid_bill_past_due_listed_as_overdue(client, customer, bill):
    # due date 2026-02-16 is in the past relative to the test run
    assert client.get("/api/bills", headers=customer[1]).json()[0]["status"] == "OVERDUE"


def test_TC_A36_get_unknown_bill(client, admin):
    assert client.get("/api/bills/9999", headers=admin).status_code == 404


# ---------------- Leak alerts ----------------
def test_TC_A37_high_usage_creates_alert(client, admin, customer, connection):
    add_reading(client, admin, connection, 0, "2026-01-01")
    add_reading(client, admin, connection, 150, "2026-02-01")
    client.post("/api/bills/generate", headers=admin, json={"connection_id": connection})
    alerts = client.get("/api/alerts", headers=customer[1]).json()
    assert len(alerts) == 1 and "High usage" in alerts[0]["message"]


def test_TC_A38_normal_usage_no_alert(client, customer, bill):
    assert client.get("/api/alerts", headers=customer[1]).json() == []


def test_TC_A39_spike_vs_history_creates_alert(client, admin, customer, connection):
    add_reading(client, admin, connection, 0, "2026-01-01")
    add_reading(client, admin, connection, 10, "2026-02-01")
    client.post("/api/bills/generate", headers=admin, json={"connection_id": connection})
    add_reading(client, admin, connection, 50, "2026-03-01")        # 40 kL vs 10 kL history
    client.post("/api/bills/generate", headers=admin, json={"connection_id": connection})
    assert len(client.get("/api/alerts", headers=customer[1]).json()) == 1


# ---------------- Payments ----------------
def pay(client, headers, bill_id, amount, paid_on=None):
    body = {"amount": amount}
    if paid_on:
        body["paid_on"] = paid_on
    return client.post(f"/api/bills/{bill_id}/pay", headers=headers, json=body)


def test_TC_A40_pay_on_time_exact_amount(client, customer, bill):
    r = pay(client, customer[1], bill["id"], 240, "2026-02-10")
    assert r.status_code == 200 and r.json()["status"] == "PAID" and r.json()["late_fee"] == 0


def test_TC_A41_pay_on_due_date_has_no_late_fee(client, customer, bill):
    assert pay(client, customer[1], bill["id"], 240, "2026-02-16").json()["late_fee"] == 0


def test_TC_A42_pay_late_requires_fee(client, customer, bill):
    assert pay(client, customer[1], bill["id"], 240, "2026-02-17").status_code == 400
    r = pay(client, customer[1], bill["id"], 269.8, "2026-02-17")
    assert r.status_code == 200 and r.json()["late_fee"] == 29.8


def test_TC_A43_underpayment_rejected(client, customer, bill):
    assert pay(client, customer[1], bill["id"], 239.99, "2026-02-10").status_code == 400


def test_TC_A44_overpayment_rejected(client, customer, bill):
    assert pay(client, customer[1], bill["id"], 240.01, "2026-02-10").status_code == 400


def test_TC_A45_double_payment_rejected(client, customer, bill):
    pay(client, customer[1], bill["id"], 240, "2026-02-10")
    assert pay(client, customer[1], bill["id"], 240, "2026-02-10").status_code == 409


def test_TC_A46_cannot_pay_someone_elses_bill(client, bill):
    client.post("/api/auth/register", json={"username": "carol", "password": "secret1", "full_name": "Carol"})
    h2 = {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": "carol", "password": "secret1"}).json()["token"]}
    assert pay(client, h2, bill["id"], 240, "2026-02-10").status_code == 403


def test_TC_A47_pay_unknown_bill(client, admin):
    assert pay(client, admin, 9999, 10).status_code == 404


def test_TC_A48_overdue_bill_can_be_paid(client, customer, bill):
    client.get("/api/bills", headers=customer[1])                    # triggers OVERDUE refresh
    assert pay(client, customer[1], bill["id"], 269.8, "2026-02-17").json()["status"] == "PAID"


def test_TC_A49_commercial_bill_uses_multiplier(client, admin, customer):
    cid, _ = customer
    k = client.post("/api/connections", headers=admin, json={
        "customer_id": cid, "meter_no": "COM001", "type": "COMMERCIAL", "address": "9 Mall Rd"}).json()["id"]
    add_reading(client, admin, k, 0, "2026-01-01")
    add_reading(client, admin, k, 20, "2026-02-01")
    b = client.post("/api/bills/generate", headers=admin, json={"connection_id": k}).json()
    assert b["water_charge"] == 195 and b["total"] == 345          # 130*1.5 + 150


# ---------------- Tariff calculator endpoint ----------------
def test_TC_A50_calculator_ok(client):
    r = client.get("/api/tariff/calculate", params={"units": 25, "type": "DOMESTIC"})
    assert r.status_code == 200 and r.json()["total"] == 240


@pytest.mark.parametrize("tc,params,code", [
    ("TC-A51", {"units": -1}, 422),
    ("TC-A52", {"units": "abc"}, 422),
    ("TC-A53", {"units": 10, "type": "INDUSTRIAL"}, 422),
    ("TC-A54", {"units": "inf"}, 422),
])
def test_calculator_invalid_inputs(client, tc, params, code):
    assert client.get("/api/tariff/calculate", params=params).status_code == code
