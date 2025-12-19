import sqlite3
from pathlib import Path

DB_PATH = Path("data/app.db")

def get_conn():
    """
    Centralized DB connection helper
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def column_exists(conn, table, column):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return column in [row[1] for row in cur.fetchall()]


def table_exists(conn, table):
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cur.fetchone() is not None


def migrate_company_schema(conn):
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            plan TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            invoice_number TEXT NOT NULL,
            vendor TEXT,
            invoice_date TEXT,
            subtotal REAL,
            tax REAL,
            total_amount REAL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, invoice_number)
        )
    """)

    # ---- CREATE COMPANIES TABLE (SAFE) ----
    # cur.execute("""
    # CREATE TABLE IF NOT EXISTS companies (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     name TEXT UNIQUE NOT NULL,
    #     gst_number TEXT,
    #     plan TEXT DEFAULT 'free',
    #     is_active INTEGER DEFAULT 1,
    #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    # )
    # """)

    # # ---- CHECK IF OLD COLUMN EXISTS ----
    # if not column_exists(conn, "users", "company_name"):
    #     # Migration already applied → do nothing
    #     return

    # # ---- INSERT COMPANIES FROM USERS ----
    # cur.execute("""
    # INSERT OR IGNORE INTO companies (name)
    # SELECT DISTINCT company_name
    # FROM users
    # WHERE company_name IS NOT NULL
    #   AND company_name != ''
    # """)

    # # ---- CREATE NEW USERS TABLE ----
    # cur.execute("""
    # CREATE TABLE users_new (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     email TEXT UNIQUE NOT NULL,
    #     password_hash TEXT NOT NULL,
    #     company_id INTEGER NOT NULL,
    #     role TEXT DEFAULT 'user',
    #     plan TEXT DEFAULT 'free',
    #     is_active INTEGER DEFAULT 1,
    #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #     FOREIGN KEY (company_id) REFERENCES companies(id)
    # )
    # """)

    # # ---- MIGRATE USERS ----
    # cur.execute("""
    # INSERT INTO users_new (
    #     id, email, password_hash, company_id, role, plan, created_at
    # )
    # SELECT
    #     u.id,
    #     u.email,
    #     u.password_hash,
    #     c.id,
    #     u.role,
    #     u.plan,
    #     u.created_at
    # FROM users u
    # JOIN companies c
    #   ON u.company_name = c.name
    # """)

    # # ---- SWAP TABLES ----
    # cur.execute("DROP TABLE users")
    # cur.execute("ALTER TABLE users_new RENAME TO users")

    conn.commit()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    migrate_company_schema(conn)
    conn.close()
