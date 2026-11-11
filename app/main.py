import hashlib
import os
import secrets
import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import billing
from . import complaints as cmp
from .db import get_conn, init_db

app = FastAPI(title="Smart Water Supply and Billing System", version="1.0.0")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TOKEN_TTL_HOURS = 8
MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 15
PAYMENT_METHODS = "^(UPI|CARD|NETBANKING|CASH)$"


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
            "SELECT u.* FROM users u JOIN tokens t ON t.user_id=u.id "
            "WHERE t.token=? AND t.expires_at>?", (token, datetime.utcnow().isoformat()),
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
    reading: float = Field(ge=0, allow_inf_nan=False)
    read_on: Optional[date] = None


class GenerateIn(BaseModel):
    connection_id: int


class PayIn(BaseModel):
    amount: float = Field(allow_inf_nan=False)
    paid_on: Optional[date] = None
    method: str = Field("UPI", pattern=PAYMENT_METHODS)


class ProfileIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=80)


class PasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=64)


class ComplaintIn(BaseModel):
    category: str = Field(pattern="^(LEAK|BILLING|NO_SUPPLY|OTHER)$")
    description: str = Field(min_length=10, max_length=500)
    connection_id: Optional[int] = None


class ComplaintUpdate(BaseModel):
    status: str = Field(pattern="^(IN_PROGRESS|RESOLVED)$")
    resolution: Optional[str] = Field(None, max_length=500)


# ---------- auth ----------
@app.post("/api/auth/register", status_code=201)
def register(body: RegisterIn):
    try:
        with get_conn() as c:
            cur = c.execute(
                "INSERT INTO users(username,password_hash,full_name,role) VALUES(?,?,?,'CUSTOMER')",
                (body.username.lower(), hash_password(body.password), body.full_name),
            )
            return {"id": cur.lastrowid, "username": body.username.lower(), "role": "CUSTOMER"}
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Username already exists")


@app.post("/api/auth/login")
def login(body: LoginIn):
    with get_conn() as c:
        row = c.execute("SELECT * FROM users WHERE username=?", (body.username.lower(),)).fetchone()
        now = datetime.utcnow()
        if row and row["locked_until"] and row["locked_until"] > now.isoformat():
            raise HTTPException(423, f"Account locked after {MAX_FAILED_LOGINS} failed attempts. "
                                     f"Try again in {LOCK_MINUTES} minutes.")
        if not row or not verify_password(body.password, row["password_hash"]):
            if row:
                attempts = row["failed_attempts"] + 1
                if attempts >= MAX_FAILED_LOGINS:
                    until = (now + timedelta(minutes=LOCK_MINUTES)).isoformat()
                    c.execute("UPDATE users SET failed_attempts=0, locked_until=? WHERE id=?", (until, row["id"]))
                    c.commit()          # persist before raising (an exception inside `with` rolls back)
                    raise HTTPException(423, f"Account locked after {MAX_FAILED_LOGINS} failed attempts. "
                                             f"Try again in {LOCK_MINUTES} minutes.")
                c.execute("UPDATE users SET failed_attempts=? WHERE id=?", (attempts, row["id"]))
                c.commit()
            raise HTTPException(401, "Invalid username or password")
        c.execute("UPDATE users SET failed_attempts=0, locked_until=NULL WHERE id=?", (row["id"],))
        token = secrets.token_hex(16)
        expires = (datetime.utcnow() + timedelta(hours=TOKEN_TTL_HOURS)).isoformat()
        c.execute("INSERT INTO tokens(token,user_id,expires_at) VALUES(?,?,?)", (token, row["id"], expires))
    return {"token": token, "role": row["role"], "user_id": row["id"], "full_name": row["full_name"]}


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None), user=Depends(current_user)):
    with get_conn() as c:
        c.execute("DELETE FROM tokens WHERE token=?", (authorization[7:],))
    return {"detail": "Logged out"}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return {k: user[k] for k in ("id", "username", "full_name", "role")}


@app.put("/api/me")
def update_profile(body: ProfileIn, user=Depends(current_user)):
    name = body.full_name.strip()
    if not name:
        raise HTTPException(422, "Full name cannot be blank")
    with get_conn() as c:
        c.execute("UPDATE users SET full_name=? WHERE id=?", (name, user["id"]))
    return {"id": user["id"], "username": user["username"], "full_name": name, "role": user["role"]}


@app.post("/api/me/password")
def change_password(body: PasswordIn, authorization: Optional[str] = Header(None), user=Depends(current_user)):
    if not verify_password(body.current_password, user["password_hash"]):
        raise HTTPException(400, "Current password is incorrect")
    if body.new_password == body.current_password:
        raise HTTPException(400, "New password must be different from the current password")
    with get_conn() as c:
        c.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(body.new_password), user["id"]))
        # sign out every other session; keep the one that made the change
        c.execute("DELETE FROM tokens WHERE user_id=? AND token<>?", (user["id"], authorization[7:]))
    return {"detail": "Password changed"}


@app.get("/api/customers")
def list_customers(_=Depends(admin_only)):
    with get_conn() as c:
        rows = c.execute("SELECT id,username,full_name FROM users WHERE role='CUSTOMER' ORDER BY id").fetchall()
    return [dict(r) for r in rows]


# ---------- tariff ----------
@app.get("/api/tariff/calculate")
def calculate(units: float = Query(..., ge=0, allow_inf_nan=False), type: str = Query("DOMESTIC", pattern="^(DOMESTIC|COMMERCIAL)$")):
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
    if read_on > date.today():
        raise HTTPException(400, "Reading date cannot be in the future")
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
        c.execute("INSERT INTO payments(bill_id,amount,late_fee,paid_on,method,paid_by) VALUES(?,?,?,?,?,?)",
                  (bill_id, due_amount, fee, paid_on.isoformat(), body.method, user["id"]))
        updated = c.execute("SELECT * FROM bills WHERE id=?", (bill_id,)).fetchone()
        return dict(updated)


# ---------- payments & receipts ----------
PAYMENT_SELECT = """
    SELECT p.id, p.bill_id, p.amount, p.late_fee, p.paid_on, p.method,
           b.units, b.water_charge, b.fixed_charge, b.total AS bill_total, b.bill_date, b.due_date,
           k.meter_no, k.type AS connection_type, k.address, k.customer_id, u.full_name AS customer_name
    FROM payments p JOIN bills b ON b.id=p.bill_id
    JOIN connections k ON k.id=b.connection_id JOIN users u ON u.id=k.customer_id"""


def _payment_out(row) -> dict:
    d = dict(row)
    d["receipt_no"] = f"RCP-{d['id']:06d}"
    return d


@app.get("/api/payments")
def list_payments(user=Depends(current_user)):
    with get_conn() as c:
        if user["role"] == "ADMIN":
            rows = c.execute(PAYMENT_SELECT + " ORDER BY p.id DESC").fetchall()
        else:
            rows = c.execute(PAYMENT_SELECT + " WHERE k.customer_id=? ORDER BY p.id DESC", (user["id"],)).fetchall()
    return [_payment_out(r) for r in rows]


@app.get("/api/payments/{payment_id}")
def get_receipt(payment_id: int, user=Depends(current_user)):
    with get_conn() as c:
        row = c.execute(PAYMENT_SELECT + " WHERE p.id=?", (payment_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Payment not found")
    if user["role"] != "ADMIN" and row["customer_id"] != user["id"]:
        raise HTTPException(403, "Not your payment")
    return _payment_out(row)


# ---------- complaints ----------
COMPLAINT_SELECT = """
    SELECT m.*, u.full_name AS customer_name, k.meter_no
    FROM complaints m JOIN users u ON u.id=m.customer_id LEFT JOIN connections k ON k.id=m.connection_id"""


@app.post("/api/complaints", status_code=201)
def file_complaint(body: ComplaintIn, user=Depends(current_user)):
    if user["role"] != "CUSTOMER":
        raise HTTPException(403, "Only customers can file complaints")
    with get_conn() as c:
        if body.connection_id is not None:
            conn = c.execute("SELECT customer_id FROM connections WHERE id=?", (body.connection_id,)).fetchone()
            if not conn:
                raise HTTPException(404, "Connection not found")
            if conn["customer_id"] != user["id"]:
                raise HTTPException(403, "Not your connection")
        today = date.today().isoformat()
        cur = c.execute(
            "INSERT INTO complaints(customer_id,connection_id,category,description,status,created_on,updated_on) "
            "VALUES(?,?,?,?,'OPEN',?,?)",
            (user["id"], body.connection_id, body.category, body.description.strip(), today, today))
        return dict(c.execute(COMPLAINT_SELECT + " WHERE m.id=?", (cur.lastrowid,)).fetchone())


@app.get("/api/complaints")
def list_complaints(user=Depends(current_user)):
    with get_conn() as c:
        if user["role"] == "ADMIN":
            rows = c.execute(COMPLAINT_SELECT + " ORDER BY m.id DESC").fetchall()
        else:
            rows = c.execute(COMPLAINT_SELECT + " WHERE m.customer_id=? ORDER BY m.id DESC", (user["id"],)).fetchall()
    return [dict(r) for r in rows]


@app.patch("/api/complaints/{complaint_id}")
def update_complaint(complaint_id: int, body: ComplaintUpdate, _=Depends(admin_only)):
    with get_conn() as c:
        row = c.execute("SELECT * FROM complaints WHERE id=?", (complaint_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Complaint not found")
        try:
            new_status = cmp.next_status(row["status"], body.status)
        except ValueError:
            raise HTTPException(409, f"Cannot move a {row['status']} complaint to {body.status}")
        resolution = (body.resolution or "").strip()
        if new_status == "RESOLVED" and len(resolution) < cmp.MIN_RESOLUTION_LENGTH:
            raise HTTPException(400, "A resolution note is required to resolve a complaint")
        c.execute("UPDATE complaints SET status=?, resolution=?, updated_on=? WHERE id=?",
                  (new_status, resolution or row["resolution"], date.today().isoformat(), complaint_id))
        return dict(c.execute(COMPLAINT_SELECT + " WHERE m.id=?", (complaint_id,)).fetchone())


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
