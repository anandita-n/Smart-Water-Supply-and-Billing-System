"""Login lock-out (TC-A73 .. TC-A78) and profile / password change (TC-A93 .. TC-A102, TC-A108)."""
import pytest

from app.db import get_conn
from conftest import _login


def attempt(client, username, password):
    return client.post("/api/auth/login", json={"username": username, "password": password}).status_code


# ---------------- login lock-out ----------------
def test_TC_A73_account_locks_on_fifth_failed_attempt(client, customer):
    assert [attempt(client, "alice", "wrong") for _ in range(5)] == [401, 401, 401, 401, 423]


def test_TC_A74_correct_password_rejected_while_locked(client, customer):
    for _ in range(5):
        attempt(client, "alice", "wrong")
    assert attempt(client, "alice", "secret1") == 423


def test_TC_A75_successful_login_resets_the_failure_counter(client, customer):
    for _ in range(4):
        attempt(client, "alice", "wrong")
    assert attempt(client, "alice", "secret1") == 200
    assert [attempt(client, "alice", "wrong") for _ in range(4)] == [401, 401, 401, 401]


def test_TC_A76_lock_expires_after_the_lock_period(client, customer):
    for _ in range(5):
        attempt(client, "alice", "wrong")
    with get_conn() as c:
        c.execute("UPDATE users SET locked_until='2000-01-01T00:00:00' WHERE username='alice'")
    assert attempt(client, "alice", "secret1") == 200


def test_TC_A77_unknown_username_is_never_reported_as_locked(client):
    assert {attempt(client, "nobody", "x") for _ in range(8)} == {401}


def test_TC_A78_lockout_affects_only_the_targeted_account(client, customer):
    client.post("/api/auth/register", json={"username": "bob", "password": "secret1", "full_name": "Bob"})
    for _ in range(5):
        attempt(client, "alice", "wrong")
    assert attempt(client, "bob", "secret1") == 200


# ---------------- profile ----------------
def test_TC_A93_update_full_name(client, customer):
    r = client.put("/api/me", headers=customer[1], json={"full_name": "  Alice Smith "})
    assert r.status_code == 200 and r.json()["full_name"] == "Alice Smith"
    assert client.get("/api/me", headers=customer[1]).json()["full_name"] == "Alice Smith"


def test_TC_A94_empty_full_name_rejected(client, customer):
    assert client.put("/api/me", headers=customer[1], json={"full_name": ""}).status_code == 422


def test_TC_A95_change_password_success(client, customer):
    r = client.post("/api/me/password", headers=customer[1],
                    json={"current_password": "secret1", "new_password": "brandnew1"})
    assert r.status_code == 200
    assert attempt(client, "alice", "secret1") == 401
    assert attempt(client, "alice", "brandnew1") == 200


def test_TC_A96_wrong_current_password_rejected(client, customer):
    r = client.post("/api/me/password", headers=customer[1],
                    json={"current_password": "nope", "new_password": "brandnew1"})
    assert r.status_code == 400
    assert attempt(client, "alice", "secret1") == 200               # unchanged


def test_TC_A97_new_password_must_differ_from_current(client, customer):
    r = client.post("/api/me/password", headers=customer[1],
                    json={"current_password": "secret1", "new_password": "secret1"})
    assert r.status_code == 400


def test_TC_A98_new_password_too_short(client, customer):
    r = client.post("/api/me/password", headers=customer[1],
                    json={"current_password": "secret1", "new_password": "12345"})
    assert r.status_code == 422


def test_TC_A108_new_password_of_minimum_length_accepted(client, customer):
    r = client.post("/api/me/password", headers=customer[1],
                    json={"current_password": "secret1", "new_password": "123456"})
    assert r.status_code == 200


def test_TC_A99_password_change_signs_out_other_sessions(client, customer):
    other = _login(client, "alice", "secret1")                       # a second session
    client.post("/api/me/password", headers=customer[1],
                json={"current_password": "secret1", "new_password": "brandnew1"})
    assert client.get("/api/me", headers=other).status_code == 401
    assert client.get("/api/me", headers=customer[1]).status_code == 200


def test_TC_A100_profile_endpoints_require_login(client):
    assert client.put("/api/me", json={"full_name": "X"}).status_code == 401
    assert client.post("/api/me/password", json={"current_password": "a", "new_password": "bbbbbb"}).status_code == 401


# ---------------- blank names (negative tests) ----------------
def test_TC_A101_whitespace_only_name_rejected_at_registration(client):
    r = client.post("/api/auth/register", json={"username": "blanky", "password": "secret1", "full_name": "    "})
    assert r.status_code == 422


def test_TC_A102_whitespace_only_name_rejected_in_profile(client, customer):
    assert client.put("/api/me", headers=customer[1], json={"full_name": "   "}).status_code == 422
