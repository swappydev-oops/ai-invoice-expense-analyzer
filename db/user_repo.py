import sqlite3
import hashlib
from pathlib import Path

DB_PATH = Path("data/app.db")

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------------------------------------
# ENSURE USERS TABLE + COLUMNS
# -------------------------------------------------
def ensure_users_schema():
    conn = get_conn()
    cur = conn.cursor()

    # Base table (original schema)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            company_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Check existing columns
    cur.execute("PRAGMA table_info(users)")
    cols = [c[1] for c in cur.fetchall()]

    if "role" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")

    if "plan" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")

    conn.commit()
    conn.close()

# -------------------------------------------------
# READ USERS
# -------------------------------------------------
def get_all_users():
    ensure_users_schema()

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT
            id,
            email,
            COALESCE(company_name, '') AS company_name,
            COALESCE(role, 'user') AS role,
            COALESCE(plan, 'free') AS plan,
            created_at
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()
    conn.close()
    return rows

# -------------------------------------------------
# CREATE USER
# -------------------------------------------------
def create_user(email, password, role, company_name="", plan="free"):
    ensure_users_schema()

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO users (email, password_hash, company_name, role, plan)
        VALUES (?, ?, ?, ?, ?)
        """,
        (email, hash_password(password), company_name, role, plan),
    )
    conn.commit()
    conn.close()

# -------------------------------------------------
# UPDATE ROLE
# -------------------------------------------------
def update_user_role(user_id, role):
    ensure_users_schema()

    conn = get_conn()
    conn.execute(
        "UPDATE users SET role=? WHERE id=?",
        (role, user_id),
    )
    conn.commit()
    conn.close()

# -------------------------------------------------
# DELETE USER
# -------------------------------------------------
def delete_user(user_id):
    ensure_users_schema()

    conn = get_conn()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
