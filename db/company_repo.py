from db.db import get_conn


def get_all_companies():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name
        FROM companies
        WHERE is_active = 1
        ORDER BY name
        """
    )

    rows = cur.fetchall()
    conn.close()
    return rows
