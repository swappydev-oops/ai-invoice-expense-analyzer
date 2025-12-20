from db.db import get_conn


def get_all_companies(include_inactive=True):
    conn = get_conn()
    cur = conn.cursor()

    if include_inactive:
        cur.execute("""
            SELECT id, name, gst_number, plan, is_active, created_at
            FROM companies
            ORDER BY created_at DESC
        """)
    else:
        cur.execute("""
            SELECT id, name, gst_number, plan, is_active, created_at
            FROM companies
            WHERE is_active = 1
            ORDER BY created_at DESC
        """)

    rows = cur.fetchall()
    conn.close()
    return rows


def create_company(name, gst_number, plan):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO companies (name, gst_number, plan, is_active)
        VALUES (?, ?, ?, 1)
    """, (name, gst_number, plan))

    conn.commit()
    conn.close()


def update_company(company_id, name, gst_number, plan):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE companies
        SET name = ?, gst_number = ?, plan = ?
        WHERE id = ?
    """, (name, gst_number, plan, company_id))

    conn.commit()
    conn.close()


def set_company_active(company_id, is_active):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE companies
        SET is_active = ?
        WHERE id = ?
    """, (is_active, company_id))

    conn.commit()
    conn.close()
