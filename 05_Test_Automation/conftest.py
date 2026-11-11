import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """A fresh, empty database for every test."""
    monkeypatch.setenv("WATER_DB", str(tmp_path / "test.db"))
    with TestClient(app) as c:
        yield c


def _login(client, username, password):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["token"]}


@pytest.fixture()
def admin(client):
    return _login(client, "admin", "admin123")


@pytest.fixture()
def customer(client):
    """Returns (customer_id, auth_headers)."""
    r = client.post("/api/auth/register",
                    json={"username": "alice", "password": "secret1", "full_name": "Alice"})
    assert r.status_code == 201
    return r.json()["id"], _login(client, "alice", "secret1")


@pytest.fixture()
def connection(client, admin, customer):
    """A DOMESTIC connection owned by alice."""
    cid, _ = customer
    r = client.post("/api/connections", headers=admin, json={
        "customer_id": cid, "meter_no": "MTR001", "type": "DOMESTIC", "address": "12 Lake Road"})
    assert r.status_code == 201
    return r.json()["id"]


def add_reading(client, admin, conn_id, value, read_on):
    return client.post("/api/readings", headers=admin,
                       json={"connection_id": conn_id, "reading": value, "read_on": read_on})


@pytest.fixture()
def bill(client, admin, connection):
    """A generated bill: 25 kL used -> Rs 240 total, due 2026-02-16."""
    add_reading(client, admin, connection, 100, "2026-01-01")
    add_reading(client, admin, connection, 125, "2026-02-01")
    r = client.post("/api/bills/generate", headers=admin, json={"connection_id": connection})
    assert r.status_code == 201
    return r.json()
