import sqlite3
import hashlib

DB_PATH = "data/app.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- INTERNAL: ENSURE COLUMNS ----------
def _ensure_user_columns():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(users)")
    cols = [c[1] for c in cur.fetchall()]

    if "plan" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")

    if "created_at" not in cols:
        cur.execute(
            "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )

    conn.commit()
    conn.close()

# ---------- READ ----------
def get_all_users():
    _ensure_user_columns()

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT
            id,
            email,
            role,
            COALESCE(plan, 'free') AS plan,
            COALESCE(created_at, '') AS created_at
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()
    conn.close()
    return rows

# ---------- CREATE ----------
def create_user(email, password, role, plan="free"):
    _ensure_user_columns()

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
    conn = get_conn()
    conn.execute(
        "UPDATE users SET role=? WHERE id=?",
        (role, user_id),
    )
    conn.commit()
    conn.close()

# ---------- DELETE ----------
def delete_user(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
