import pandas as pd
from db.db import get_connection

# -------------------------------------------------
# DUPLICATE CHECK
# -------------------------------------------------
def invoice_exists(user_id, invoice_number):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM invoices WHERE user_id = ? AND invoice_number = ?",
        (user_id, invoice_number)
    )
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

# -------------------------------------------------
# INSERT
# -------------------------------------------------
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

# -------------------------------------------------
# READ
# -------------------------------------------------
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

# -------------------------------------------------
# UPDATE
# -------------------------------------------------
def update_invoice(invoice_id, row: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE invoices SET
            invoice_number = ?,
            invoice_date = ?,
            subtotal = ?,
            gst_percent = ?,
            gst_amount = ?,
            total_amount = ?,
            category = ?
        WHERE id = ?
        """,
        (
            row["invoice_number"],
            row["date"],
            row["subtotal"],
            row["gst_percent"],
            row["tax"],
            row["total_amount"],
            row["category"],
            invoice_id
        )
    )
    conn.commit()
    conn.close()

# -------------------------------------------------
# DELETE
# -------------------------------------------------
def delete_invoice(invoice_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()

# -------------------------------------------------
# MONTHLY GST SUMMARY
# -------------------------------------------------
def get_monthly_gst_summary(user_id):
    conn = get_connection()
    df = pd.read_sql(
        """
        SELECT
            strftime('%Y-%m', invoice_date) AS month,
            SUM(subtotal) AS taxable_amount,
            SUM(gst_amount) AS gst_amount,
            SUM(total_amount) AS total_amount
        FROM invoices
        WHERE user_id = ?
        GROUP BY month
        ORDER BY month
        """,
        conn,
        params=(user_id,)
    )
    conn.close()
    return df

# -------------------------------------------------
# VENDOR-WISE SPEND
# -------------------------------------------------
def get_vendor_spend(user_id):
    conn = get_connection()
    df = pd.read_sql(
        """
        SELECT
            invoice_number AS vendor,
            SUM(total_amount) AS total_spend
        FROM invoices
        WHERE user_id = ?
        GROUP BY vendor
        ORDER BY total_spend DESC
        """,
        conn,
        params=(user_id,)
    )
    conn.close()
    return df

# -------------------------------------------------
# CATEGORY ANALYTICS
# -------------------------------------------------
def get_category_spend(user_id):
    conn = get_connection()
    df = pd.read_sql(
        """
        SELECT
            category,
            SUM(total_amount) AS total_spend
        FROM invoices
        WHERE user_id = ?
        GROUP BY category
        ORDER BY total_spend DESC
        """,
        conn,
        params=(user_id,)
    )
    conn.close()
    return df
