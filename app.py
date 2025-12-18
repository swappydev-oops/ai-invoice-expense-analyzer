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
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="AI Invoice & Expense Analyzer",
    layout="wide"
)

# -------------------------------------------------
# THEME (DARK / LIGHT)
# -------------------------------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

def apply_theme(dark):
    if dark:
        st.markdown("""
        <style>
        body { background-color: #0e1117; color: #fafafa; }
        .kpi-card { background:#161b22; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        body { background-color: #ffffff; color: #262730; }
        .kpi-card { background:#f6f8fa; }
        </style>
        """, unsafe_allow_html=True)

apply_theme(st.session_state.dark_mode)

# -------------------------------------------------
# GLOBAL UI CSS
# -------------------------------------------------
st.markdown("""
<style>
.kpi-card {
    padding: 1.5rem;
    border-radius: 14px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    text-align: center;
}
.kpi-title {
    font-size: 0.9rem;
    color: #6b7280;
}
.kpi-value {
    font-size: 1.8rem;
    font-weight: 700;
    margin-top: 0.3rem;
}
button[kind="primary"] {
    background: linear-gradient(135deg,#2563eb,#4f46e5);
    color: white;
    border-radius: 10px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# INIT
# -------------------------------------------------
init_db()
require_login()

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
with st.sidebar:
    st.markdown("### 🧾 Invoice Analyzer")
    st.markdown(f"👤 **{st.session_state.user_email}**")
    st.markdown(f"📦 Plan: `{st.session_state.plan}`")
    st.markdown(f"🔐 Role: `{st.session_state.role}`")

    st.divider()

    st.session_state.dark_mode = st.toggle(
        "🌙 Dark mode",
        value=st.session_state.dark_mode
    )

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
df = get_invoices(st.session_state.user_id)

# -------------------------------------------------
# EMPTY STATE
# -------------------------------------------------
if df.empty:
    st.markdown("""
    <div style="text-align:center; padding:4rem;">
        <h2>📭 No invoices yet</h2>
        <p style="color:#6b7280;">
            Upload your first invoice to unlock insights
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# -------------------------------------------------
# KPI CARDS
# -------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Invoices</div>
        <div class="kpi-value">📄 {len(df)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Total Spend</div>
        <div class="kpi-value">₹ {df["total_amount"].sum():,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">GST Paid</div>
        <div class="kpi-value">₹ {df["tax"].sum():,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# -------------------------------------------------
# INVOICE TABLE
# -------------------------------------------------
st.subheader("🧾 Invoices")

editable = can_edit(st.session_state.role)

edited_df = st.data_editor(
    df,
    disabled=not editable,
    use_container_width=True,
    num_rows="fixed"
)

if editable:
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Changes", type="primary", use_container_width=True):
            for _, r in edited_df.iterrows():
                update_invoice(r["id"], r.to_dict())
            st.toast("Invoices updated")

    with col2:
        del_id = st.selectbox("Delete invoice", df["id"])
        if st.button("Delete"):
            delete_invoice(del_id)
            st.rerun()

# -------------------------------------------------
# MONTHLY TREND
# -------------------------------------------------
st.subheader("📈 Monthly Spend Trend")
gst = get_monthly_gst_summary(st.session_state.user_id)
st.line_chart(gst.set_index("month")[["total_amount"]])

# -------------------------------------------------
# VENDOR DASHBOARD
# -------------------------------------------------
st.subheader("🏢 Vendor-wise Spend")
vendors = get_vendor_spend(st.session_state.user_id)
st.bar_chart(vendors.set_index("vendor"))

# -------------------------------------------------
# CATEGORY ANALYTICS
# -------------------------------------------------
st.subheader("🧩 Category Analytics")
cats = get_category_spend(st.session_state.user_id)
st.bar_chart(cats.set_index("category"))

# -------------------------------------------------
# GST REPORT
# -------------------------------------------------
st.subheader("📑 Auto GST Report")
st.json(generate_gst_report(df))

# -------------------------------------------------
# EXCEL EXPORT / IMPORT
# -------------------------------------------------
st.subheader("📂 Excel")

excel_file = export_full_excel(df, gst, vendors)
st.download_button(
    "⬇ Download Excel Report",
    excel_file,
    file_name="gst_full_report.xlsx",
    type="primary"
)

if editable:
    uploaded_excel = st.file_uploader("Upload edited Excel", type=["xlsx"])
    if uploaded_excel:
        import_excel_and_sync(uploaded_excel)
        st.toast("Excel synced")
        st.rerun()
