import streamlit as st
import pandas as pd
import time
from PIL import Image

from db.db import init_db
from auth.auth import require_login
from auth.roles import can_edit
from utils import extract_invoice_details
from utils.excel_export import export_full_excel
from utils.excel_import import import_excel_and_sync
from utils.gst_report import generate_gst_report
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
# Toast helper (safe)
# -------------------------------------------------
def show_toast(msg):
    try:
        st.toast(msg, icon="✅")
    except Exception:
        st.success(msg)

# -------------------------------------------------
# Init DB + Auth
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
    st.write(f"📦 Plan: {st.session_state.plan}")
    st.write(f"🔐 Role: {st.session_state.role}")

    if st.button("Logout"):
        st.session_state.clear()
        show_toast("Logout successful")
        time.sleep(0.3)
        st.rerun()

# -------------------------------------------------
# Title
# -------------------------------------------------
st.title("📊 AI Invoice & Expense Dashboard")

# -------------------------------------------------
# Upload Guard
# -------------------------------------------------
if "files_processed" not in st.session_state:
    st.session_state.files_processed = False

# -------------------------------------------------
# Upload Invoices
# -------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload Invoice Images / PDFs (WhatsApp downloads supported)",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)

if uploaded_files and not st.session_state.files_processed:

    added, skipped = 0, 0

    for file in uploaded_files:
        try:
            if file.type == "application/pdf":
                data = extract_invoice_details(file, "pdf")
            else:
                data = extract_invoice_details(Image.open(file), "image")

            invoice_no = data.get("invoice_number")

            if invoice_no and invoice_exists(
                st.session_state.user_id,
                invoice_no
            ):
                skipped += 1
                continue

            # Free plan enforcement
            if (
                st.session_state.plan == "free"
                and get_invoices(st.session_state.user_id).shape[0] >= 50
            ):
                st.error("Free plan limit reached (50 invoices).")
                break

            insert_invoice(st.session_state.user_id, data)
            added += 1

        except Exception as e:
            st.error(f"{file.name}: {str(e)}")

    st.session_state.files_processed = True

    if added:
        show_toast(f"{added} invoice(s) uploaded")
    if skipped:
        st.warning(f"{skipped} duplicate invoice(s) skipped")

if not uploaded_files:
    st.session_state.files_processed = False

# -------------------------------------------------
# Load invoices (canonical)
# -------------------------------------------------
df_invoices = get_invoices(st.session_state.user_id)

# -------------------------------------------------
# Invoice Table (Editable based on role)
# -------------------------------------------------
st.subheader("🧾 Invoices")

if not df_invoices.empty:

    editable = can_edit(st.session_state.role)

    edited_df = st.data_editor(
        df_invoices,
        use_container_width=True,
        num_rows="fixed",
        disabled=not editable
    )

    if editable:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save Changes"):
                for _, row in edited_df.iterrows():
                    update_invoice(row["id"], row.to_dict())
                show_toast("Invoices updated")

        with col2:
            del_id = st.selectbox(
                "🗑 Delete Invoice",
                df_invoices["id"]
            )
            if st.button("Delete"):
                delete_invoice(del_id)
                show_toast("Invoice deleted")
                st.rerun()
else:
    st.info("No invoices uploaded yet.")

# -------------------------------------------------
# GST Validation Flags (Safe numeric handling)
# -------------------------------------------------
st.subheader("⚠ GST Validation Flags")

if not df_invoices.empty:
    gst_df = df_invoices.copy()

    for col in ["subtotal", "gst_percent", "tax"]:
        gst_df[col] = (
            gst_df[col]
            .astype(str)
            .str.replace(",", "")
            .str.replace("%", "")
        )
        gst_df[col] = pd.to_numeric(
            gst_df[col], errors="coerce"
        ).fillna(0)

    gst_df["expected_gst"] = (
        gst_df["subtotal"] * gst_df["gst_percent"] / 100
    ).round(2)

    gst_df["gst_mismatch"] = (
        gst_df["expected_gst"] != gst_df["tax"]
    )

    mismatches = gst_df[gst_df["gst_mismatch"]]

    if not mismatches.empty:
        st.dataframe(mismatches, use_container_width=True)
    else:
        st.success("No GST mismatches detected")

# -------------------------------------------------
# Monthly Trend Dashboard
# -------------------------------------------------
st.subheader("📈 Monthly Spend Trend")

df_gst = get_monthly_gst_summary(st.session_state.user_id)

if not df_gst.empty:
    st.line_chart(
        df_gst.set_index("month")[["total_amount"]],
        use_container_width=True
    )

# -------------------------------------------------
# Vendor-wise Spend Dashboard
# -------------------------------------------------
st.subheader("🏢 Vendor-wise Spend")

df_vendor = get_vendor_spend(st.session_state.user_id)
if not df_vendor.empty:
    st.bar_chart(df_vendor.set_index("vendor"))

# -------------------------------------------------
# Category Analytics
# -------------------------------------------------
st.subheader("🧩 Category Analytics")

df_category = get_category_spend(st.session_state.user_id)
if not df_category.empty:
    st.bar_chart(df_category.set_index("category"))

# -------------------------------------------------
# Auto GST Report (Free format)
# -------------------------------------------------
st.subheader("📑 Auto GST Report")

if not df_invoices.empty:
    gst_report = generate_gst_report(df_invoices)
    st.json(gst_report)

# -------------------------------------------------
# Editable Excel Import
# -------------------------------------------------
if can_edit(st.session_state.role):
    st.subheader("✏ Editable Excel Sync")

    uploaded_excel = st.file_uploader(
        "Upload Edited Excel (Invoices sheet)",
        type=["xlsx"]
    )
    if uploaded_excel:
        import_excel_and_sync(uploaded_excel)
        show_toast("Excel synced with database")
        st.rerun()

# -------------------------------------------------
# Multi-sheet Excel Export
# -------------------------------------------------
if not df_invoices.empty:
    excel_file = export_full_excel(
        df_invoices,
        df_gst,
        df_vendor
    )

    st.download_button(
        "⬇ Download Full Excel Report",
        excel_file,
        file_name="gst_full_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
