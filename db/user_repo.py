from db.db import get_conn
import hashlib


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_all_users():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            u.id,
            u.user_name,
            u.email,
            c.company_name,
            u.role,
            u.is_active,
            u.created_date
        FROM users u
        LEFT JOIN companies c ON u.company_id = c.id
        ORDER BY u.created_date DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def create_user(data, admin_user):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (
            user_name,
            user_firstname,
            user_lastname,
            email,
            password_hash,
            company_id,
            role,
            is_active,
            created_by
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE,%s)
    """, (
        data["user_name"],
        data["first_name"],
        data["last_name"],
        data["email"],
        hash_password(data["password"]),
        data["company_id"],
        data["role"],
        admin_user
    ))

    conn.commit()
    conn.close()


def update_user_role(uid, role, admin_user):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET
            role = %s,
            modified_by = %s,
            modified_date = NOW()
        WHERE id = %s
    """, (role, admin_user, uid))

    conn.commit()
    conn.close()


def toggle_user(uid, is_active, admin_user):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET
            is_active = %s,
            modified_by = %s,
            modified_date = NOW()
        WHERE id = %s
    """, (is_active, admin_user, uid))

    conn.commit()
    conn.close()
