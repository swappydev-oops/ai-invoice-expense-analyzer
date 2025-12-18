import streamlit as st
import pandas as pd
from PIL import Image
import os
from io import BytesIO
from openpyxl.utils import get_column_letter
from db.db import init_db, get_connection
from auth.auth import require_login
from utils import extract_invoice_details
import time

# -------------------------------------------------
# Initialize Database & Auth
# -------------------------------------------------
init_db()
require_login()

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(
    page_title="AI Invoice & Expense Analyzer",
    layout="wide"
)

# -------------------------------------------------
# Sidebar (User + Logout)
# -------------------------------------------------
with st.sidebar:
    st.write(f"👤 {st.session_state.user_email}")

    if st.button("Logout"):
        st.session_state.clear()
        if hasattr(st, "toast"):
        st.toast("Logout successful 👋", icon="✅")
    else:
        st.success("Logout successful 👋")
    time.sleep(0.3)
    st.rerun()


# -------------------------------------------------
# Main Title
# -------------------------------------------------
st.title("🧾 AI Invoice & Expense Analyzer")

# -------------------------------------------------
# File Upload
# -------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload Invoice Images or PDFs",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)

# -------------------------------------------------
# Display Column Mapping (UI / Excel only)
# -------------------------------------------------
DISPLAY_COLUMN_MAPPING = {
    "invoice_number": "Invoice Number",
    "invoice_number_conf": "Invoice Number Confidence (%)",
    "vendor": "Vendor Name",
    "vendor_conf": "Vendor Confidence (%)",
    "date": "Invoice Date",
    "date_conf": "Date Confidence (%)",
    "subtotal": "Subtotal Amount",
    "subtotal_conf": "Subtotal Confidence (%)",
    "tax": "GST Amount",
    "gst_percent": "GST %",
    "tax_conf": "GST Confidence (%)",
    "total_amount": "Total Amount",
    "total_conf": "Total Amount Confidence (%)",
    "category": "Category",
    "source_file": "Source File"
}

# -------------------------------------------------
# Process Uploaded Invoices
# -------------------------------------------------
all_data = []

if uploaded_files:
    for file in uploaded_files:
        try:
            with st.spinner(f"Processing {file.name}..."):
                if file.type == "application/pdf":
                    record = extract_invoice_details(file, "pdf")
                else:
                    image = Image.open(file)
                    record = extract_invoice_details(image, "image")

                record["source_file"] = file.name
                all_data.append(record)

        except Exception as e:
            st.error(f"{file.name}: {str(e)}")

    if all_data:
        df_new = pd.DataFrame(all_data)

        # -------------------------------------------------
        # Store Invoices in Database (RAW)
        # -------------------------------------------------
        conn = get_connection()
        cursor = conn.cursor()

        user_id = st.session_state.user_id

        for _, row in df_new.iterrows():
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
                    row.get("invoice_number"),
                    row.get("date"),
                    row.get("subtotal"),
                    row.get("gst_percent"),
                    row.get("tax"),
                    row.get("total_amount"),
                    row.get("category"),
                    row.get("source_file")
                )
            )

        conn.commit()
        conn.close()

        st.toast(f"{len(df_new)} invoice(s) uploaded successfully 🎉", icon="✅")

# -------------------------------------------------
# Load User Invoices from DB
# -------------------------------------------------
conn = get_connection()

df_db = pd.read_sql(
    """
    SELECT
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
    params=(st.session_state.user_id,)
)

conn.close()


if not df_db.empty:
    df_display = df_db.rename(columns=DISPLAY_COLUMN_MAPPING)

    st.subheader("📊 Uploaded Invoices")
    st.dataframe(df_display, use_container_width=True)

    # -------------------------------------------------
    # Excel Export (Formatted, Multi-use)
    # -------------------------------------------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_display.to_excel(writer, index=False, sheet_name="Invoices")
        ws = writer.sheets["Invoices"]

        for idx, col in enumerate(df_display.columns, 1):
            col_letter = get_column_letter(idx)
            max_len = int(
                max(
                    df_display[col].astype(str).str.len().fillna(0).max(),
                    len(col)
                )
            )
            ws.column_dimensions[col_letter].width = max_len + 3

    output.seek(0)

    st.download_button(
        "⬇ Download Invoice History (Excel)",
        data=output,
        file_name="invoice_history.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("No invoices uploaded yet.")
