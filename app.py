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

from db.user_repo import (
    get_all_users,
    create_user,
    update_user_role,
    delete_user
)

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="AI Invoice & Expense Analyzer",
    layout="wide"
)

# -------------------------------------------------
# INIT DB + AUTH
# -------------------------------------------------
init_db()
require_login()

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
if "show_admin" not in st.session_state:
    st.session_state.show_admin = False

with st.sidebar:
    st.markdown("## 🧾 Invoice Analyzer")
    st.markdown(f"👤 **{st.session_state.user_email}**")
    st.markdown(f"🔐 Role: `{st.session_state.role}`")
    st.markdown(f"📦 Plan: `{st.session_state.plan}`")

    st.divider()

    if st.button("🛠 Admin Panel"):
        st.session_state.show_admin = True

    st.divider()

    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# -------------------------------------------------
# ADMIN PANEL (TEMP – ACCESSIBLE TO ALL USERS)
# -------------------------------------------------
if st.session_state.show_admin:
    st.title("🛠 Admin Panel – User Management")

    st.info(
        "⚠ Admin panel is temporarily open to all users. "
        "Once admin setup is complete, this will be restricted."
    )

    # -------- CREATE USER --------
    with st.expander("➕ Create User"):
        email = st.text_input("Email", key="admin_email")
        password = st.text_input("Password", type="password", key="admin_password")
        role = st.selectbox("Role", ["admin", "user"], key="admin_role")

        if st.button("Create User"):
            try:
                create_user(email, password, role)
                st.success("User created successfully")
                st.rerun()
            except Exception:
                st.error("User already exists or invalid input")

    # -------- USER LIST --------
    st.subheader("👥 Existing Users")

    users = get_all_users()

    if not users:
        st.info("No users found")
    else:
        for user_id, email, role, created_at in users:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            col1.write(email)

            new_role = col2.selectbox(
                "Role",
                ["admin", "user"],
                index=0 if role == "admin" else 1,
                key=f"role_{user_id}",
            )

            if new_role != role:
                if col3.button("Update", key=f"update_{user_id}"):
                    update_user_role(user_id, new_role)
                    st.success("Role updated")
                    st.rerun()

            if col4.button("Delete", key=f"delete_{user_id}"):
                delete_user(user_id)
                st.warning("User deleted")
                st.rerun()

    st.divider()
    if st.button("⬅ Back to Dashboard"):
        st.session_state.show_admin = False
        st.rerun()

    st.stop()

# -------------------------------------------------
# MAIN DASHBOARD
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
# KPI CARDS
# -------------------------------------------------
if not df_invoices.empty:
    col1, col2, col3 = st.columns(3)

    col1.metric("📄 Total Invoices", len(df_invoices))
    col2.metric("💰 Total Spend", f"₹ {df_invoices['total_amount'].sum():,.0f}")
    col3.metric("🧾 GST Paid", f"₹ {df_invoices['tax'].sum():,.0f}")
else:
    st.info("📭 No invoices uploaded yet")

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
        st.success(f"{added} invoice(s) uploaded")
    if skipped:
        st.warning(f"{skipped} duplicate invoice(s) skipped")

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
        disabled=not editable
    )

    if editable:
        if st.button("💾 Save Changes"):
            for _, row in edited_df.iterrows():
                update_invoice(row["id"], row.to_dict())
            st.success("Invoices updated")
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
        st.success("Excel synced")
        st.rerun()

if not df_invoices.empty:
    excel_file = export_full_excel(df_invoices, df_gst, df_vendor)
    st.download_button(
        "⬇ Download Full Excel Report",
        excel_file,
        file_name="gst_full_report.xlsx"
    )
