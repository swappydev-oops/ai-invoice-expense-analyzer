import pandas as pd
from db.db import get_connection

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
