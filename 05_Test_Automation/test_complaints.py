"""Complaints module: state machine unit tests (TC-U31..U36) and API tests (TC-A79..A92, A103..A107)."""
import pytest

from app import complaints as cm
from conftest import _login


# ---------------- state transition unit tests ----------------
def test_TC_U31_open_to_in_progress():
    assert cm.next_status("OPEN", "IN_PROGRESS") == "IN_PROGRESS"


def test_TC_U32_in_progress_to_resolved():
    assert cm.next_status("IN_PROGRESS", "RESOLVED") == "RESOLVED"


def test_TC_U33_cannot_skip_in_progress():
    with pytest.raises(ValueError):
        cm.next_status("OPEN", "RESOLVED")


def test_TC_U34_resolved_is_final():
    for target in ("OPEN", "IN_PROGRESS", "RESOLVED"):
        with pytest.raises(ValueError):
            cm.next_status("RESOLVED", target)


def test_TC_U35_cannot_move_backwards():
    with pytest.raises(ValueError):
        cm.next_status("IN_PROGRESS", "OPEN")


def test_TC_U36_allowed_next_states():
    assert cm.allowed_next("OPEN") == ["IN_PROGRESS"]
    assert cm.allowed_next("IN_PROGRESS") == ["RESOLVED"]
    assert cm.allowed_next("RESOLVED") == []


# ---------------- API tests ----------------
GOOD = {"category": "LEAK", "description": "Water is leaking near the meter."}


def file_complaint(client, headers, **extra):
    return client.post("/api/complaints", headers=headers, json={**GOOD, **extra})


def carol(client):
    client.post("/api/auth/register", json={"username": "carol", "password": "secret1", "full_name": "Carol"})
    return _login(client, "carol", "secret1")


def test_TC_A79_customer_files_complaint_for_own_connection(client, customer, connection):
    r = file_complaint(client, customer[1], connection_id=connection)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "OPEN" and body["meter_no"] == "MTR001" and body["resolution"] is None


@pytest.mark.parametrize("tc,length,code", [("TC-A80", 9, 422), ("TC-A103", 10, 201), ("TC-A104", 500, 201), ("TC-A105", 501, 422)])
def test_complaint_description_length_boundaries(client, customer, tc, length, code):
    r = client.post("/api/complaints", headers=customer[1], json={"category": "OTHER", "description": "x" * length})
    assert r.status_code == code


def test_TC_A81_invalid_category_rejected(client, customer):
    assert file_complaint(client, customer[1], category="NOISE").status_code == 422


def test_TC_A82_cannot_file_against_someone_elses_connection(client, connection):
    assert file_complaint(client, carol(client), connection_id=connection).status_code == 403


def test_TC_A83_customer_sees_only_own_complaints(client, customer):
    file_complaint(client, customer[1])
    assert len(client.get("/api/complaints", headers=customer[1]).json()) == 1
    assert client.get("/api/complaints", headers=carol(client)).json() == []


def test_TC_A84_admin_sees_all_complaints_with_customer_name(client, admin, customer):
    file_complaint(client, customer[1])
    rows = client.get("/api/complaints", headers=admin).json()
    assert len(rows) == 1 and rows[0]["customer_name"] == "Alice"


def patch(client, headers, cid, status, resolution=None):
    body = {"status": status}
    if resolution is not None:
        body["resolution"] = resolution
    return client.patch(f"/api/complaints/{cid}", headers=headers, json=body)


@pytest.fixture()
def complaint(client, customer):
    return file_complaint(client, customer[1]).json()


def test_TC_A85_admin_moves_open_to_in_progress(client, admin, complaint):
    r = patch(client, admin, complaint["id"], "IN_PROGRESS")
    assert r.status_code == 200 and r.json()["status"] == "IN_PROGRESS"


def test_TC_A86_resolving_requires_a_resolution_note(client, admin, complaint):
    patch(client, admin, complaint["id"], "IN_PROGRESS")
    assert patch(client, admin, complaint["id"], "RESOLVED").status_code == 400
    assert patch(client, admin, complaint["id"], "RESOLVED", "ab").status_code == 400      # below the 3-char minimum
    assert client.get("/api/complaints", headers=admin).json()[0]["status"] == "IN_PROGRESS"


def test_TC_A87_resolve_with_note(client, admin, customer, complaint):
    patch(client, admin, complaint["id"], "IN_PROGRESS")
    r = patch(client, admin, complaint["id"], "RESOLVED", "Replaced the faulty valve.")
    assert r.status_code == 200 and r.json()["status"] == "RESOLVED"
    assert client.get("/api/complaints", headers=customer[1]).json()[0]["resolution"] == "Replaced the faulty valve."


def test_TC_A88_cannot_resolve_an_open_complaint_directly(client, admin, complaint):
    assert patch(client, admin, complaint["id"], "RESOLVED", "Fixed it").status_code == 409


def test_TC_A89_resolved_complaint_cannot_change_again(client, admin, complaint):
    patch(client, admin, complaint["id"], "IN_PROGRESS")
    patch(client, admin, complaint["id"], "RESOLVED", "Fixed it")
    assert patch(client, admin, complaint["id"], "IN_PROGRESS").status_code == 409


def test_TC_A90_customer_cannot_update_complaints(client, customer, complaint):
    assert patch(client, customer[1], complaint["id"], "IN_PROGRESS").status_code == 403


def test_TC_A91_admin_cannot_file_complaints(client, admin):
    assert file_complaint(client, admin).status_code == 403


def test_TC_A92_unknown_complaint(client, admin):
    assert patch(client, admin, 9999, "IN_PROGRESS").status_code == 404


def test_TC_A106_status_open_is_not_an_allowed_target(client, admin, complaint):
    assert patch(client, admin, complaint["id"], "OPEN").status_code == 422


def test_TC_A107_complaint_without_a_connection_is_allowed(client, customer):
    r = file_complaint(client, customer[1], category="BILLING")
    assert r.status_code == 201 and r.json()["connection_id"] is None


def test_TC_A113_complaints_require_login(client):
    assert client.get("/api/complaints").status_code == 401
