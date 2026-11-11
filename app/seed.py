"""Load demo data: 6 customers, connections, 4 months of readings, bills and some payments.

Run from the project folder:   python -m app.seed
Safe to run twice: it stops if the demo customers already exist.
All demo customers sign in with the password  water123
"""
from datetime import date, timedelta

from fastapi.testclient import TestClient

from . import billing
from .main import app

PASSWORD = "water123"

# username, full name, type, meter, address, monthly usage in kL for the last 3 months
CUSTOMERS = [
    ("anandita", "S Anandita Narayan", "DOMESTIC", "MTR-1001", "12 Lake View Road, Bengaluru", [12, 14, 11]),
    ("vivan", "Vivan Raj Belur", "DOMESTIC", "MTR-1002", "48 Garden Street, Bengaluru", [22, 25, 19]),
    ("rohan", "Rohan Mehta", "DOMESTIC", "MTR-1003", "7 Temple Lane, Mysuru", [8, 9, 10]),
    ("priya", "Priya Nair (Nair Bakery)", "COMMERCIAL", "MTR-1004", "3 Market Road, Bengaluru", [40, 45, 38]),
    ("karthik", "Karthik Rao", "DOMESTIC", "MTR-1005", "21 Hill Park, Mangaluru", [15, 14, 62]),   # last month spikes: leak alert
    ("meera", "Meera Iyer", "DOMESTIC", "MTR-1006", "90 Rose Avenue, Bengaluru", [18, 20, 21]),
]
OPENING = [100, 200, 50, 500, 300, 150]


def first_of_month(d: date, back: int) -> date:
    y, m = d.year, d.month - back
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1)


def main():
    today = date.today()
    months = [first_of_month(today, n) for n in (3, 2, 1, 0)]      # 4 reading dates -> 3 bills each
    with TestClient(app) as c:
        admin = {"Authorization": "Bearer " + c.post("/api/auth/login", json={"username": "admin", "password": "admin123"}).json()["token"]}
        existing = {u["username"] for u in c.get("/api/customers", headers=admin).json()}
        already = bool(existing & {x[0] for x in CUSTOMERS})
        if already:
            print("Demo customers already exist - skipping customers and bills.")
        for idx, (user, name, ctype, meter, addr, usage) in enumerate([] if already else CUSTOMERS):
            cid = c.post("/api/auth/register", json={"username": user, "password": PASSWORD, "full_name": name}).json()["id"]
            conn = c.post("/api/connections", headers=admin, json={"customer_id": cid, "meter_no": meter, "type": ctype, "address": addr}).json()["id"]
            reading = OPENING[idx]
            c.post("/api/readings", headers=admin, json={"connection_id": conn, "reading": reading, "read_on": months[0].isoformat()})
            for month_no, kl in enumerate(usage, start=1):
                reading += kl
                c.post("/api/readings", headers=admin, json={"connection_id": conn, "reading": reading, "read_on": months[month_no].isoformat()})
                bill = c.post("/api/bills/generate", headers=admin, json={"connection_id": conn}).json()
                due = date.fromisoformat(bill["due_date"])
                # payment pattern: older bills paid; vivan pays October late; rohan & meera leave October unpaid
                pay_on = min(date.fromisoformat(bill["bill_date"]) + timedelta(days=5), today)
                paid = month_no == 1 or (month_no == 2 and user not in ("rohan", "meera")) or (month_no == 3 and user == "anandita")
                if paid and user == "vivan" and month_no == 2:
                    pay_on = min(due + timedelta(days=4), today)
                if paid:
                    fee = billing.late_fee(bill["total"], due, pay_on)
                    r = c.post(f"/api/bills/{bill['id']}/pay", headers=admin,
                               json={"amount": round(bill["total"] + fee, 2), "paid_on": pay_on.isoformat()})
                    assert r.status_code == 200, r.text
        seed_complaints(c, admin)
        bills = c.get("/api/bills", headers=admin).json()
        print(f"Customers: {len(CUSTOMERS)}, bills: {len(bills)}, complaints: {len(c.get('/api/complaints', headers=admin).json())}."
              f" Customer password: {PASSWORD}")


# username, category, description, what the admin has done: None / "IN_PROGRESS" / resolution note
COMPLAINTS = [
    ("karthik", "LEAK", "Water keeps running even when all taps are closed. Possible leak after the meter.", "IN_PROGRESS"),
    ("rohan", "BILLING", "My October bill looks higher than my usual usage. Please check the reading.", None),
    ("meera", "NO_SUPPLY", "No water supply in our lane since the morning.", "Valve repaired at the street junction. Supply restored."),
    ("anandita", "OTHER", "Please update the contact details on my connection.", None),
]


def seed_complaints(c, admin):
    if c.get("/api/complaints", headers=admin).json():
        return                                            # already has complaints
    for user, category, text, action in COMPLAINTS:
        token = c.post("/api/auth/login", json={"username": user, "password": PASSWORD}).json().get("token")
        if not token:
            continue                                      # demo customer missing or password changed
        h = {"Authorization": "Bearer " + token}
        conn = next(iter(c.get("/api/connections", headers=h).json()), None)
        body = {"category": category, "description": text}
        if conn:
            body["connection_id"] = conn["id"]
        cid = c.post("/api/complaints", headers=h, json=body).json()["id"]
        if action:
            c.patch(f"/api/complaints/{cid}", headers=admin, json={"status": "IN_PROGRESS"})
        if action and action != "IN_PROGRESS":
            c.patch(f"/api/complaints/{cid}", headers=admin, json={"status": "RESOLVED", "resolution": action})


if __name__ == "__main__":
    main()
