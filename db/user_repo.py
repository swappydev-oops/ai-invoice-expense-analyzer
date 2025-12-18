import sqlite3
import hashlib

DB_PATH = "db/database.db"

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ---------- CRUD OPERATIONS ----------

def get_all_users():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, email, role, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return rows

def create_user(email, password, role):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, hash_password(password), role),
        )
        conn.commit()
    except Exception as e:
        raise e
    finally:
        conn.close()

def update_user_role(user_id, role):
    conn = get_conn()
    conn.execute(
        "UPDATE users SET role=? WHERE id=?",
        (role, user_id),
    )
    conn.commit()
    conn.close()

def delete_user(user_id):
    conn = get_conn()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
