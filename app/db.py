import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('ADMIN','CUSTOMER'))
);
CREATE TABLE IF NOT EXISTS tokens(token TEXT PRIMARY KEY, user_id INTEGER NOT NULL);
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
