import streamlit as st
import pandas as pd
import time
from PIL import Image
from io import BytesIO
from openpyxl.utils import get_column_letter

from db.db import init_db
from auth.auth import require_login
from utils import extract_invoice_details
from db.invoice_repo import (
    insert_invoice,
    get_invoices,
    update_invoice,
    delete_invoice,
    get_monthly_gst_summary,
    invoice_exists
)

# -------------------------------------------------
# Safe Toast Helper (Streamlit version compatible)
# -------------------------------------------------
def show_toast(message):
    try:
        st.toast(message, icon="✅")
    except Exception:
        st.success(message)

# -------------------------------------------------
# Initialize DB & Authentication
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
# Sidebar (User Info + Logout)
# -------------------------------------------------
with st.sidebar:
    st.write(f"👤 {st.session_state.user_email}")

    if st.button("Logout"):
        st.session_state.clear()
        show_toast("Logout successful 👋")
        time.sleep(0.3)
        st.rerun()

# -------------------------------------------------
# Main Title
# -------------------------------------------------
st.title("🧾 AI Invoice & Expense Analyzer")

# -------------------------------------------------
# Session Guard (prevents duplicate inserts on rerun)
# -------------------------------------------------
if "files_processed" not in st.session_state:
    st.session_state.files_processed = False

# -------------------------------------------------
# File Upload
# -------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload Invoice Images or PDFs",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)

# -------------------------------------------------
# Upload & OCR Processing → DB (with DUPLICATE VALIDATION)
# -------------------------------------------------
if uploaded_files and not st.session_state.files_processed:

    inserted_count = 0
    skipped_count = 0

    for file in uploaded_files:
        try:
            with st.spinner(f"Processing {file.name}..."):

                if file.type == "application/pdf":
                    data = extract_invoice_details(file, "pdf")
                else:
                    image = Image.open(file)
                    data = extract_invoice_details(image, "image")

                data["source_file"] = file.name
                invoice_no = data.get("invoice_number")

                # ---- DUPLICATE CHECK (PER USER) ----
                if invoice_no and invoice_exists(
                    st.session_state.user_id,
                    invoice_no
                ):
                    skipped_count += 1
                    continue

                insert_invoice(
                    user_id=st.session_state.user_id,
                    data=data
                )
                inserted_count += 1

        except Exception as e:
            st.error(f"{file.name}: {str(e)}")

    st.session_state.files_processed = True

    # ---- USER FEEDBACK ----
    if inserted_count > 0:
        show_toast(f"{inserted_count} invoice(s) uploaded successfully 🎉")

    if skipped_count > 0:
        st.warning(
            f"{skipped_count} invoice(s) were already uploaded and were skipped."
        )

# -------------------------------------------------
# Reset upload flag when uploader is cleared
# -------------------------------------------------
if not uploaded_files:
    st.session_state.files_processed = False

# -------------------------------------------------
# Load Invoices (USER-SCOPED)
# -------------------------------------------------
df_db = get_invoices(st.session_state.user_id)

# -------------------------------------------------
# Invoice Management (Edit / Delete)
# -------------------------------------------------
st.subheader("📊 Uploaded Invoices")

if not df_db.empty:

    edited_df = st.data_editor(
        df_db,
        use_container_width=True,
        num_rows="fixed",
        key="invoice_editor"
    )

    col1, col2 = st.columns(2)

    # ---------------- Save Changes ----------------
    with col1:
        if st.button("💾 Save Changes"):
            for _, row in edited_df.iterrows():
                update_invoice(row["id"], row.to_dict())
            show_toast("Invoices updated successfully")

    # ---------------- Delete Invoice ----------------
    with col2:
        invoice_to_delete = st.selectbox(
            "🗑 Select Invoice ID to delete",
            df_db["id"].tolist()
        )

        if st.button("Delete Invoice"):
            delete_invoice(invoice_to_delete)
            show_toast("Invoice deleted")
            st.rerun()

else:
    st.info("No invoices uploaded yet.")

# -------------------------------------------------
# Monthly GST Dashboard (SAFE & DEFENSIVE)
# -------------------------------------------------
st.subheader("📅 Monthly GST Summary")

df_gst = get_monthly_gst_summary(st.session_state.user_id)

if not df_gst.empty:

    selected_month = st.selectbox(
        "Select Month",
        df_gst["month"].tolist()
    )

    filtered = df_gst[df_gst["month"] == selected_month]

    if not filtered.empty:
        row = filtered.iloc[0]

        c1, c2, c3 = st.columns(3)
        c1.metric("Taxable Amount", f"₹ {row['taxable_amount']:,}")
        c2.metric("GST Amount", f"₹ {row['gst_amount']:,}")
        c3.metric("Total Spend", f"₹ {row['total_amount']:,}")
    else:
        st.warning("No data available for selected month.")

    st.bar_chart(
        df_gst.set_index("month")[["gst_amount"]],
        use_container_width=True
    )

else:
    st.info("No GST data available yet.")

# -------------------------------------------------
# Multi-Sheet GST Excel Export
# -------------------------------------------------
if not df_db.empty:

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        # Sheet 1: Invoices
        df_db.drop(columns=["id"]).to_excel(
            writer, index=False, sheet_name="Invoices"
        )

        # Sheet 2: Monthly GST Summary
        df_gst.to_excel(
            writer, index=False, sheet_name="Monthly_GST_Summary"
        )

        ws = writer.sheets["Invoices"]

        for idx, col in enumerate(df_db.drop(columns=["id"]).columns, 1):
            col_letter = get_column_letter(idx)
            max_len = max(
                df_db[col].astype(str).map(len).max(),
                len(col)
            )
            ws.column_dimensions[col_letter].width = max_len + 3

    output.seek(0)

    st.download_button(
        "⬇ Download GST Report (Excel)",
        data=output,
        file_name="gst_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# -------------------------------------------------
# GST VALIDATION FLAGS
# -------------------------------------------------
st.subheader("⚠ GST Validation")

if not df.empty:
    df["expected_gst"] = (df["subtotal"] * df["gst_percent"] / 100).round(2)
    df["gst_mismatch"] = df["expected_gst"] != df["tax"]
    st.dataframe(df[df["gst_mismatch"]])

# -------------------------------------------------
# VENDOR SPEND
# -------------------------------------------------
st.subheader("🏢 Vendor-wise Spend")

vendors = get_vendor_spend(st.session_state.user_id)
if not vendors.empty:
    st.bar_chart(vendors.set_index("vendor"))

# -------------------------------------------------
# CATEGORY ANALYTICS
# -------------------------------------------------
st.subheader("🧩 Category Analytics")

cats = get_category_spend(st.session_state.user_id)
if not cats.empty:
    st.bar_chart(cats.set_index("category"))
