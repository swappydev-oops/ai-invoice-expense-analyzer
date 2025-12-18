import pandas as pd
from db.db import get_connection
from db.invoice_repo import get_monthly_gst_summary


# ---------------- CREATE ----------------

def insert_invoice(user_id, data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO invoices (
            user_id, invoice_number, invoice_date,
            subtotal, gst_percent, gst_amount,
            total_amount, category, source_file
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            data.get("invoice_number"),
            data.get("date"),
            data.get("subtotal"),
            data.get("gst_percent"),
            data.get("tax"),
            data.get("total_amount"),
            data.get("category"),
            data.get("source_file"),
        )
    )

    conn.commit()
    conn.close()

# ---------------- READ ----------------

def get_invoices(user_id):
    conn = get_connection()
    df = pd.read_sql(
        """
        SELECT
            id,
            invoice_number,
            invoice_date AS date,
            subtotal,
            gst_amount AS tax,
            gst_percent,
            total_amount,
            category,
            source_file
        FROM invoices
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        conn,
        params=(user_id,)
    )
    conn.close()
    return df

# ---------------- UPDATE ----------------

def update_invoice(invoice_id, updated_row: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE invoices
        SET invoice_number = ?,
            invoice_date = ?,
            subtotal = ?,
            gst_percent = ?,
            gst_amount = ?,
            total_amount = ?,
            category = ?
        WHERE id = ?
        """,
        (
            updated_row["invoice_number"],
            updated_row["date"],
            updated_row["subtotal"],
            updated_row["gst_percent"],
            updated_row["tax"],
            updated_row["total_amount"],
            updated_row["category"],
            invoice_id
        )
    )

    conn.commit()
    conn.close()

# ---------------- DELETE ----------------

def delete_invoice(invoice_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()

def get_monthly_gst_summary(user_id):
    conn = get_connection()
    df = pd.read_sql(
        """
        SELECT
            strftime('%Y-%m', invoice_date) AS month,
            ROUND(SUM(subtotal), 2) AS taxable_amount,
            ROUND(SUM(gst_amount), 2) AS gst_amount,
            ROUND(SUM(total_amount), 2) AS total_amount
        FROM invoices
        WHERE user_id = ?
        GROUP BY month
        ORDER BY month DESC
        """,
        conn,
        params=(user_id,)
    )
    conn.close()
    return df

