import sqlite3
import hashlib
from db.config import DB_PATH

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def get_all_users():
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT id, email, role, plan, created_at
        FROM users
        ORDER BY id DESC
        """
    ).fetchall()
    conn.close()
    return rows

def create_user(email, password, role, plan="free"):
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
    conn.execute(
        "DELETE FROM users WHERE id=?",
        (user_id,),
    )
    conn.commit()
    conn.close()
