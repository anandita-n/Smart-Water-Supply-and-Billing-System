import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('ADMIN','CUSTOMER')),
  failed_attempts INTEGER NOT NULL DEFAULT 0,
  locked_until TEXT
);
CREATE TABLE IF NOT EXISTS payments(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  bill_id INTEGER UNIQUE NOT NULL,
  amount REAL NOT NULL,
  late_fee REAL NOT NULL DEFAULT 0,
  paid_on TEXT NOT NULL,
  method TEXT NOT NULL DEFAULT 'UPI',
  paid_by INTEGER
);
CREATE TABLE IF NOT EXISTS complaints(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER NOT NULL,
  connection_id INTEGER,
  category TEXT NOT NULL,
  description TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'OPEN',
  resolution TEXT,
  created_on TEXT NOT NULL,
  updated_on TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tokens(
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  expires_at TEXT NOT NULL DEFAULT '2000-01-01T00:00:00'
);
CREATE TABLE IF NOT EXISTS connections(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_id INTEGER NOT NULL,
  meter_no TEXT UNIQUE NOT NULL,
  type TEXT NOT NULL,
  address TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS readings(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  connection_id INTEGER NOT NULL,
  reading REAL NOT NULL,
  read_on TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bills(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  connection_id INTEGER NOT NULL,
  reading_id INTEGER UNIQUE NOT NULL,
  units REAL NOT NULL,
  water_charge REAL NOT NULL,
  fixed_charge REAL NOT NULL,
  total REAL NOT NULL,
  bill_date TEXT NOT NULL,
  due_date TEXT NOT NULL,
  status TEXT NOT NULL,
  late_fee REAL NOT NULL DEFAULT 0,
  paid_on TEXT
);
CREATE TABLE IF NOT EXISTS alerts(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  connection_id INTEGER NOT NULL,
  message TEXT NOT NULL,
  created_on TEXT NOT NULL
);
"""


def db_path() -> str:
    return os.environ.get("WATER_DB", "water.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as c:
        c.executescript(SCHEMA)
        # migrate databases created before token expiry existed (DEF-003)
        cols = [r["name"] for r in c.execute("PRAGMA table_info(tokens)")]
        if "expires_at" not in cols:
            c.execute("ALTER TABLE tokens ADD COLUMN expires_at TEXT NOT NULL DEFAULT '2000-01-01T00:00:00'")
        # migrate databases created before login lock-out existed
        ucols = [r["name"] for r in c.execute("PRAGMA table_info(users)")]
        if "failed_attempts" not in ucols:
            c.execute("ALTER TABLE users ADD COLUMN failed_attempts INTEGER NOT NULL DEFAULT 0")
        if "locked_until" not in ucols:
            c.execute("ALTER TABLE users ADD COLUMN locked_until TEXT")
        # bills paid before the payments table existed get a payment record too
        c.execute("""INSERT INTO payments(bill_id,amount,late_fee,paid_on,method)
                     SELECT id, total+late_fee, late_fee, COALESCE(paid_on,bill_date), 'UPI'
                     FROM bills WHERE status='PAID' AND id NOT IN (SELECT bill_id FROM payments)""")
