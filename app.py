import streamlit as st
import pandas as pd
import time
from PIL import Image
from io import BytesIO

from db.db import init_db
from auth.auth import require_login
from utils import extract_invoice_details
from db.invoice_repo import (
    insert_invoice,
    invoice_exists,
    get_invoices,
    update_invoice,
    delete_invoice,
    get_monthly_gst_summary,
    get_vendor_spend,
    get_category_spend
)

# -------------------------------------------------
# Safe Toast Helper
# -------------------------------------------------
def show_toast(message):
    try:
        st.toast(message, icon="✅")
    except Exception:
        st.success(message)

# -------------------------------------------------
# Init DB & Auth
# -------------------------------------------------
init_db()
require_login()

st.set_page_config(
    page_title="AI Invoice & Expense Analyzer",
    layout="wide"
)

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
with st.sidebar:
    st.write(f"👤 {st.session_state.user_email}")
    if st.button("Logout"):
        st.session_state.clear()
        show_toast("Logout successful 👋")
        time.sleep(0.3)
        st.rerun()

# -------------------------------------------------
# Title
# -------------------------------------------------
st.title("📊 AI Invoice & Expense Dashboard")

# -------------------------------------------------
# Upload session guard
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
# Upload & OCR Processing (with duplicate validation)
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

                if invoice_no and invoice_exists(
                    st.session_state.user_id,
                    invoice_no
                ):
                    skipped_count += 1
                    continue

                insert_invoice(st.session_state.user_id, data)
                inserted_count += 1

        except Exception as e:
            st.error(f"{file.name}: {str(e)}")

    st.session_state.files_processed = True

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
# Load invoices ONCE (canonical variable)
# -------------------------------------------------
df_invoices = get_invoices(st.session_state.user_id)

# -------------------------------------------------
# Invoice Management
# -------------------------------------------------
st.subheader("🧾 Invoices")

if not df_invoices.empty:

    edited_df = st.data_editor(
        df_invoices,
        use_container_width=True,
        num_rows="fixed",
        key="invoice_editor"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Changes"):
            for _, row in edited_df.iterrows():
                update_invoice(row["id"], row.to_dict())
            show_toast("Invoices updated successfully")

    with col2:
        invoice_to_delete = st.selectbox(
            "🗑 Select Invoice ID to delete",
            df_invoices["id"].tolist()
        )
        if st.button("Delete Invoice"):
            delete_invoice(invoice_to_delete)
            show_toast("Invoice deleted")
            st.rerun()

else:
    st.info("No invoices uploaded yet.")

# -------------------------------------------------
# GST VALIDATION FLAGS
# -------------------------------------------------
st.subheader("⚠ GST Validation Flags")

if not df_invoices.empty:
    gst_df = df_invoices.copy()
    gst_df["expected_gst"] = (
        gst_df["subtotal"] * gst_df["gst_percent"] / 100
    ).round(2)
    gst_df["gst_mismatch"] = gst_df["expected_gst"] != gst_df["tax"]

    mismatches = gst_df[gst_df["gst_mismatch"]]

    if not mismatches.empty:
        st.dataframe(mismatches, use_container_width=True)
    else:
        st.success("No GST mismatches found 🎉")

# -------------------------------------------------
# Monthly Trend Line
# -------------------------------------------------
st.subheader("📈 Monthly Spend Trend")

df_gst = get_monthly_gst_summary(st.session_state.user_id)

if not df_gst.empty:
    st.line_chart(
        df_gst.set_index("month")[["total_amount"]],
        use_container_width=True
    )

# -------------------------------------------------
# Vendor-wise Spend
# -------------------------------------------------
st.subheader("🏢 Vendor-wise Spend")

df_vendor = get_vendor_spend(st.session_state.user_id)

if not df_vendor.empty:
    st.bar_chart(
        df_vendor.set_index("vendor"),
        use_container_width=True
    )

# -------------------------------------------------
# Category Analytics
# -------------------------------------------------
st.subheader("🧩 Category-wise Spend")

df_category = get_category_spend(st.session_state.user_id)

if not df_category.empty:
    st.bar_chart(
        df_category.set_index("category"),
        use_container_width=True
    )
