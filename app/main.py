import hashlib
import os
import secrets
import sqlite3
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import billing
from .db import get_conn, init_db

app = FastAPI(title="Smart Water Supply and Billing System", version="1.0.0")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


# ---------- helpers ----------
def hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 50_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    salt, _ = stored.split("$", 1)
    return secrets.compare_digest(hash_password(password, salt), stored)


@app.on_event("startup")
def startup():
    init_db()
    with get_conn() as c:
        if not c.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
            c.execute(
                "INSERT INTO users(username,password_hash,full_name,role) VALUES(?,?,?,?)",
                ("admin", hash_password("admin123"), "System Administrator", "ADMIN"),
            )


def current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid token")
    token = authorization[7:]
    with get_conn() as c:
        row = c.execute(
            "SELECT u.* FROM users u JOIN tokens t ON t.user_id=u.id WHERE t.token=?", (token,)
        ).fetchone()
    if not row:
        raise HTTPException(401, "Invalid token")
    return dict(row)


def admin_only(user=Depends(current_user)):
    if user["role"] != "ADMIN":
        raise HTTPException(403, "Admin access required")
    return user


# ---------- schemas ----------
class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=64)
    full_name: str = Field(min_length=1, max_length=80)


class LoginIn(BaseModel):
    username: str
    password: str


class ConnectionIn(BaseModel):
    customer_id: int
    meter_no: str = Field(min_length=3, max_length=20)
    type: str = Field(pattern=r"^(DOMESTIC|COMMERCIAL)$")
    address: str = Field(min_length=3, max_length=200)


class ReadingIn(BaseModel):
    connection_id: int
    reading: float = Field(ge=0)
    read_on: Optional[date] = None


class GenerateIn(BaseModel):
    connection_id: int


class PayIn(BaseModel):
    amount: float
    paid_on: Optional[date] = None


# ---------- auth ----------
@app.post("/api/auth/register", status_code=201)
def register(body: RegisterIn):
    try:
        with get_conn() as c:
            cur = c.execute(
                "INSERT INTO users(username,password_hash,full_name,role) VALUES(?,?,?,'CUSTOMER')",
                (body.username, hash_password(body.password), body.full_name),
            )
            return {"id": cur.lastrowid, "username": body.username, "role": "CUSTOMER"}
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Username already exists")


@app.post("/api/auth/login")
def login(body: LoginIn):
    with get_conn() as c:
        row = c.execute("SELECT * FROM users WHERE username=?", (body.username,)).fetchone()
        if not row or not verify_password(body.password, row["password_hash"]):
            raise HTTPException(401, "Invalid username or password")
        token = secrets.token_hex(16)
        c.execute("INSERT INTO tokens(token,user_id) VALUES(?,?)", (token, row["id"]))
    return {"token": token, "role": row["role"], "user_id": row["id"], "full_name": row["full_name"]}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return {k: user[k] for k in ("id", "username", "full_name", "role")}


# ---------- tariff ----------
@app.get("/api/tariff/calculate")
def calculate(units: float = Query(..., ge=0), type: str = Query("DOMESTIC", pattern="^(DOMESTIC|COMMERCIAL)$")):
    return {"units": units, "type": type, **billing.bill_total(units, type)}


# ---------- connections ----------
@app.post("/api/connections", status_code=201)
def create_connection(body: ConnectionIn, _=Depends(admin_only)):
    with get_conn() as c:
        cust = c.execute("SELECT role FROM users WHERE id=?", (body.customer_id,)).fetchone()
        if not cust or cust["role"] != "CUSTOMER":
            raise HTTPException(404, "Customer not found")
        try:
            cur = c.execute(
                "INSERT INTO connections(customer_id,meter_no,type,address) VALUES(?,?,?,?)",
                (body.customer_id, body.meter_no, body.type, body.address),
            )
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Meter number already in use")
        return {"id": cur.lastrowid, **body.model_dump()}


@app.get("/api/connections")
def list_connections(user=Depends(current_user)):
    with get_conn() as c:
        if user["role"] == "ADMIN":
            rows = c.execute("SELECT * FROM connections").fetchall()
        else:
            rows = c.execute("SELECT * FROM connections WHERE customer_id=?", (user["id"],)).fetchall()
    return [dict(r) for r in rows]


# ---------- readings ----------
@app.post("/api/readings", status_code=201)
def add_reading(body: ReadingIn, _=Depends(admin_only)):
    read_on = body.read_on or date.today()
    with get_conn() as c:
        conn = c.execute("SELECT * FROM connections WHERE id=?", (body.connection_id,)).fetchone()
        if not conn:
            raise HTTPException(404, "Connection not found")
        last = c.execute(
            "SELECT * FROM readings WHERE connection_id=? ORDER BY id DESC LIMIT 1", (body.connection_id,)
        ).fetchone()
        if last and body.reading < last["reading"]:
            raise HTTPException(400, "Reading cannot be lower than the previous reading")
        if last and read_on.isoformat() < last["read_on"]:
            raise HTTPException(400, "Reading date cannot be earlier than the previous reading date")
        cur = c.execute(
            "INSERT INTO readings(connection_id,reading,read_on) VALUES(?,?,?)",
            (body.connection_id, body.reading, read_on.isoformat()),
        )
        return {"id": cur.lastrowid, "connection_id": body.connection_id,
                "reading": body.reading, "read_on": read_on.isoformat()}


# ---------- bills ----------
def _refresh_overdue(c: sqlite3.Connection):
    today = date.today().isoformat()
    rows = c.execute("SELECT id,status FROM bills WHERE status='UNPAID' AND due_date<?", (today,)).fetchall()
    for r in rows:
        c.execute("UPDATE bills SET status=? WHERE id=?", (billing.next_status(r["status"], "due_passed"), r["id"]))


@app.post("/api/bills/generate", status_code=201)
def generate_bill(body: GenerateIn, _=Depends(admin_only)):
    with get_conn() as c:
        conn = c.execute("SELECT * FROM connections WHERE id=?", (body.connection_id,)).fetchone()
        if not conn:
            raise HTTPException(404, "Connection not found")
        reads = c.execute(
            "SELECT * FROM readings WHERE connection_id=? ORDER BY id", (body.connection_id,)
        ).fetchall()
        if len(reads) < 2:
            raise HTTPException(400, "At least two readings are required to generate a bill")
        latest, prev = reads[-1], reads[-2]
        if c.execute("SELECT 1 FROM bills WHERE reading_id=?", (latest["id"],)).fetchone():
            raise HTTPException(409, "Bill already generated for the latest reading")
        units = round(latest["reading"] - prev["reading"], 2)
        amounts = billing.bill_total(units, conn["type"])
        bill_date = date.fromisoformat(latest["read_on"])
        due = billing.due_date_for(bill_date)
        previous_units = [r["units"] for r in c.execute(
            "SELECT units FROM bills WHERE connection_id=?", (body.connection_id,)).fetchall()]
        cur = c.execute(
            """INSERT INTO bills(connection_id,reading_id,units,water_charge,fixed_charge,total,
               bill_date,due_date,status) VALUES(?,?,?,?,?,?,?,?,'UNPAID')""",
            (body.connection_id, latest["id"], units, amounts["water_charge"], amounts["fixed_charge"],
             amounts["total"], bill_date.isoformat(), due.isoformat()),
        )
        if billing.is_leak_suspected(units, previous_units):
            c.execute(
                "INSERT INTO alerts(connection_id,message,created_on) VALUES(?,?,?)",
                (body.connection_id, f"High usage detected: {units} kL", date.today().isoformat()),
            )
        row = c.execute("SELECT * FROM bills WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


@app.get("/api/bills")
def list_bills(user=Depends(current_user)):
    with get_conn() as c:
        _refresh_overdue(c)
        if user["role"] == "ADMIN":
            rows = c.execute("SELECT * FROM bills ORDER BY id").fetchall()
        else:
            rows = c.execute(
                """SELECT b.* FROM bills b JOIN connections k ON k.id=b.connection_id
                   WHERE k.customer_id=? ORDER BY b.id""", (user["id"],)).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/bills/{bill_id}")
def get_bill(bill_id: int, user=Depends(current_user)):
    with get_conn() as c:
        _refresh_overdue(c)
        row = c.execute(
            """SELECT b.*, k.customer_id FROM bills b JOIN connections k ON k.id=b.connection_id
               WHERE b.id=?""", (bill_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Bill not found")
    if user["role"] != "ADMIN" and row["customer_id"] != user["id"]:
        raise HTTPException(403, "Not your bill")
    return dict(row)


@app.post("/api/bills/{bill_id}/pay")
def pay_bill(bill_id: int, body: PayIn, user=Depends(current_user)):
    paid_on = body.paid_on or date.today()
    with get_conn() as c:
        row = c.execute(
            """SELECT b.*, k.customer_id FROM bills b JOIN connections k ON k.id=b.connection_id
               WHERE b.id=?""", (bill_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Bill not found")
        if user["role"] != "ADMIN" and row["customer_id"] != user["id"]:
            raise HTTPException(403, "Not your bill")
        if row["status"] == "PAID":
            raise HTTPException(409, "Bill already paid")
        fee = billing.late_fee(row["total"], date.fromisoformat(row["due_date"]), paid_on)
        due_amount = round(row["total"] + fee, 2)
        if round(body.amount, 2) != due_amount:
            raise HTTPException(400, f"Amount must equal the amount due: {due_amount}")
        c.execute("UPDATE bills SET status=?, late_fee=?, paid_on=? WHERE id=?",
                  (billing.next_status(row["status"], "pay"), fee, paid_on.isoformat(), bill_id))
        updated = c.execute("SELECT * FROM bills WHERE id=?", (bill_id,)).fetchone()
        return dict(updated)


# ---------- alerts ----------
@app.get("/api/alerts")
def list_alerts(user=Depends(current_user)):
    with get_conn() as c:
        if user["role"] == "ADMIN":
            rows = c.execute("SELECT * FROM alerts ORDER BY id").fetchall()
        else:
            rows = c.execute(
                """SELECT a.* FROM alerts a JOIN connections k ON k.id=a.connection_id
                   WHERE k.customer_id=? ORDER BY a.id""", (user["id"],)).fetchall()
    return [dict(r) for r in rows]


# ---------- UI ----------
@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
