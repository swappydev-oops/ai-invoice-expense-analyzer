import sqlite3
import hashlib
from pathlib import Path

DB_PATH = Path("data/app.db")

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- ENSURE USERS TABLE ----------
def _ensure_users_table():
    conn = get_conn()
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

    conn.commit()
    conn.close()

# ---------- READ ----------
def get_all_users():
    _ensure_users_table()

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT
            id,
            email,
            role,
            COALESCE(plan, 'free'),
            COALESCE(created_at, '')
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()
    conn.close()
    return rows

# ---------- CREATE ----------
def create_user(email, password, role, plan="free"):
    _ensure_users_table()

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO users (email, password_hash, role, plan)
        VALUES (?, ?, ?, ?)
        """,
        (email, hash_password(password), role, plan),
    )
    conn.commit()
    conn.close()

# ---------- UPDATE ----------
def update_user_role(user_id, role):
    _ensure_users_table()

    conn = get_conn()
    conn.execute(
        "UPDATE users SET role=? WHERE id=?",
        (role, user_id),
    )
    conn.commit()
    conn.close()

# ---------- DELETE ----------
def delete_user(user_id):
    _ensure_users_table()

    conn = get_conn()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
