import streamlit as st
import pandas as pd
import time
from PIL import Image

from db.db import init_db
from auth.auth import require_login
from auth.roles import can_edit
from utils import extract_invoice_details
from helpers.excel_export import export_full_excel
from helpers.excel_import import import_excel_and_sync
from helpers.gst_report import generate_gst_report
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
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="AI Invoice & Expense Analyzer",
    layout="wide"
)

# -------------------------------------------------
# THEME + UI STYLES
# -------------------------------------------------
def apply_theme(dark_mode: bool):
    if dark_mode:
        bg = "#0e1117"
        card = "#161b22"
        text = "#fafafa"
    else:
        bg = "#ffffff"
        card = "#f6f8fa"
        text = "#262730"

    st.markdown(f"""
    <style>
    body {{
        background-color: {bg};
        color: {text};
    }}

    .kpi-card {{
        background: {card};
        padding: 1.5rem;
        border-radius: 14px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        text-align: center;
    }}

    .kpi-title {{
        font-size: 0.85rem;
        color: #6b7280;
    }}

    .kpi-value {{
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 0.4rem;
    }}

    button[kind="primary"] {{
        background: linear-gradient(135deg, #2563eb, #4f46e5);
        color: white;
        border-radius: 10px;
        font-weight: 600;
    }}
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# INIT DB + AUTH
# -------------------------------------------------
init_db()
require_login()

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

with st.sidebar:
    st.markdown("## 🧾 Invoice Analyzer")
    st.markdown(f"👤 **{st.session_state.user_email}**")
    st.markdown(f"📦 Plan: `{st.session_state.plan}`")
    st.markdown(f"🔐 Role: `{st.session_state.role}`")

    st.divider()

    st.session_state.dark_mode = st.toggle(
        "🌙 Dark mode",
        value=st.session_state.dark_mode
    )

    apply_theme(st.session_state.dark_mode)

    st.divider()

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# -------------------------------------------------
# TITLE
# -------------------------------------------------
st.title("📊 Dashboard")

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
df_invoices = get_invoices(st.session_state.user_id)
df_gst = get_monthly_gst_summary(st.session_state.user_id)
df_vendor = get_vendor_spend(st.session_state.user_id)
df_category = get_category_spend(st.session_state.user_id)

# -------------------------------------------------
# KPI DASHBOARD
# -------------------------------------------------
if not df_invoices.empty:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Invoices</div>
            <div class="kpi-value">📄 {len(df_invoices)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Spend</div>
            <div class="kpi-value">₹ {df_invoices["total_amount"].sum():,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">GST Paid</div>
            <div class="kpi-value">₹ {df_invoices["tax"].sum():,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="text-align:center; padding:4rem;">
        <h2>📭 No invoices yet</h2>
        <p style="color:#6b7280;">
            Upload your first invoice to unlock insights
        </p>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------
# UPLOAD INVOICES
# -------------------------------------------------
st.subheader("📤 Upload Invoices")

uploaded_files = st.file_uploader(
    "Upload invoice images or PDFs",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    added, skipped = 0, 0
    for file in uploaded_files:
        data = (
            extract_invoice_details(file, "pdf")
            if file.type == "application/pdf"
            else extract_invoice_details(Image.open(file), "image")
        )

        if invoice_exists(st.session_state.user_id, data["invoice_number"]):
            skipped += 1
            continue

        insert_invoice(st.session_state.user_id, data)
        added += 1

    if added:
        st.toast(f"{added} invoices uploaded 🎉")
    if skipped:
        st.warning(f"{skipped} duplicates skipped")

    st.rerun()

# -------------------------------------------------
# INVOICE TABLE
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
        if st.button("💾 Save Changes", type="primary", use_container_width=True):
            for _, row in edited_df.iterrows():
                update_invoice(row["id"], row.to_dict())
            st.toast("Invoices updated")
else:
    st.info("No invoices available")

# -------------------------------------------------
# CHARTS
# -------------------------------------------------
st.subheader("📈 Monthly Trend")
if not df_gst.empty:
    st.line_chart(df_gst.set_index("month")[["total_amount"]])

st.subheader("🏢 Vendor-wise Spend")
if not df_vendor.empty:
    st.bar_chart(df_vendor.set_index("vendor"))

st.subheader("🧩 Category Analytics")
if not df_category.empty:
    st.bar_chart(df_category.set_index("category"))

# -------------------------------------------------
# GST REPORT
# -------------------------------------------------
st.subheader("📑 GST Summary")
if not df_invoices.empty:
    st.json(generate_gst_report(df_invoices))

# -------------------------------------------------
# EXCEL IMPORT / EXPORT
# -------------------------------------------------
st.subheader("📂 Excel")

if can_edit(st.session_state.role):
    uploaded_excel = st.file_uploader("Upload edited Excel", type=["xlsx"])
    if uploaded_excel:
        import_excel_and_sync(uploaded_excel)
        st.toast("Excel synced")
        st.rerun()

if not df_invoices.empty:
    excel_file = export_full_excel(df_invoices, df_gst, df_vendor)
    st.download_button(
        "⬇ Download Full Excel Report",
        excel_file,
        file_name="gst_full_report.xlsx",
        type="primary"
    )
