from db.db import get_conn


def get_all_companies():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            company_name,
            gst_number,
            subscription_plan,
            is_active,
            created_date
        FROM companies
        ORDER BY created_date DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def create_company(name, gst, plan, admin_user):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO companies (
            company_name,
            gst_number,
            subscription_plan,
            is_active,
            created_by
        )
        VALUES (%s, %s, %s, TRUE, %s)
    """, (name, gst, plan, admin_user))

    conn.commit()
    conn.close()


def update_company(cid, name, gst, plan, admin_user):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE companies
        SET
            company_name = %s,
            gst_number = %s,
            subscription_plan = %s,
            modified_by = %s,
            modified_date = NOW()
        WHERE id = %s
    """, (name, gst, plan, admin_user, cid))

    conn.commit()
    conn.close()


def toggle_company(cid, is_active, admin_user):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE companies
        SET
            is_active = %s,
            modified_by = %s,
            modified_date = NOW()
        WHERE id = %s
    """, (is_active, admin_user, cid))

    conn.commit()
    conn.close()
