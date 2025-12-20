import streamlit as st
import pandas as pd
import time
from PIL import Image

from db.db import init_db
from auth.auth import require_login
from utils import extract_invoice_details
from db.company_repo import get_all_companies

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


init_db()

#----------------------------------------
#  Temp Code
# ---------------------------------------

# import sqlite3
# from pathlib import Path

# DB_PATH = Path("data/app.db")

# st.subheader("🔍 SQLite Schema Debug")

# if DB_PATH.exists():
#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.cursor()

#     cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
#     st.write("Tables:", cur.fetchall())

#     cur.execute("PRAGMA table_info(users)")
#     st.write("Users table:", cur.fetchall())

#     cur.execute("PRAGMA table_info(companies)")
#     st.write("Companies table:", cur.fetchall())

#     conn.close()
# else:
#     st.error("DB file does not exist")


# -------------------------------------------------
# Safe Toast Helper
# -------------------------------------------------
def show_toast(message):
    try:
        st.toast(message, icon="✅")
    except Exception:
        st.success(message)

# -------------------------------------------------
# Init
# -------------------------------------------------
st.set_page_config(
    page_title="Invoice & Expense Analyzer",
    layout="wide"
)

require_login()

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.user_email}**")

    st.divider()

    # 🔽 Admin Section (Expandable)
    with st.expander("🛠 Admin Panel", expanded=False):

        if st.button("👥 User Details", use_container_width=True):
            st.session_state.page = "admin_users"

        if st.button("🏢 Company Details", use_container_width=True):
            st.session_state.page = "admin_companies"

    st.divider()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        toast("Logged out")
        time.sleep(0.3)
        st.rerun()


# =================================================
# ADMIN – USER DETAILS (EXISTING CRUD PAGE)
# =================================================
if st.session_state.page == "admin_users":
    st.title("🛠 Admin Panel – User Management")

    with st.expander("➕ Create New User"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        companies = get_all_companies()
        if not companies:
            st.warning("No companies available")
            st.stop()

        company_map = {name: cid for cid, name in companies}
        company_name = st.selectbox("Company", list(company_map.keys()))
        company_id = company_map[company_name]

        role = st.selectbox("Role", ["admin", "user"])
        plan = st.selectbox("Plan", ["free", "pro"])

        if st.button("Create User"):
            create_user(email, password, company_id, role, plan)
            toast("User created")
            st.rerun()

    st.divider()
    st.subheader("👥 Users")

    users = get_all_users()

    header = st.columns([3, 3, 2, 2, 2])
    header[0].markdown("**Email**")
    header[1].markdown("**Company**")
    header[2].markdown("**Plan**")
    header[3].markdown("**Role**")
    header[4].markdown("**Action**")

    for user_id, email, company, role, plan, is_active, created_at in users:
        cols = st.columns([3, 3, 2, 2, 2])
        cols[0].write(email)
        cols[1].write(company)
        cols[2].write(plan)

        new_role = cols[3].selectbox(
            "Role",
            ["admin", "user"],
            index=0 if role == "admin" else 1,
            key=f"role_{user_id}",
            label_visibility="collapsed"
        )

        if cols[4].button("💾 Update", key=f"upd_{user_id}"):
            update_user_role(user_id, new_role)
            toast("Role updated")
            st.rerun()

        if cols[4].button("❌ Delete", key=f"del_{user_id}"):
            delete_user(user_id)
            toast("User deleted")
            st.rerun()

    st.stop()

# # =================================================
# # ADMIN – COMPANY DETAILS
# # =================================================
# if st.session_state.page == "admin_companies":
#     st.title("🏢 Company Management")

#     from db.company_repo import (
#         get_all_companies,
#         create_company,
#         update_company,
#         set_company_active
#     )

#     # ---------------- CREATE COMPANY ----------------
#     with st.expander("➕ Create New Company"):
#         name = st.text_input("Company Name")
#         gst = st.text_input("GST Number")
#         plan = st.selectbox("Plan", ["free", "pro"])

#         if st.button("Create Company"):
#             if not name:
#                 st.error("Company name is required")
#             else:
#                 create_company(name, gst, plan)
#                 toast("Company created")
#                 st.rerun()

#     st.divider()
#     st.subheader("🏢 Companies")

#     companies = get_all_companies()

#     if not companies:
#         st.info("No companies found")
#         st.stop()

#     # ---- TABLE HEADER ----
#     header = st.columns([3, 2, 2, 2, 2])
#     header[0].markdown("**Name**")
#     header[1].markdown("**GST**")
#     header[2].markdown("**Plan**")
#     header[3].markdown("**Status**")
#     header[4].markdown("**Action**")

#     # ---- TABLE ROWS ----
#     for cid, name, gst, plan, is_active, created_at in companies:
#         cols = st.columns([3, 2, 2, 2, 2])

#         cols[0].write(name)
#         cols[1].write(gst or "-")
#         cols[2].write(plan)
#         cols[3].write("✅ Active" if is_active else "❌ Disabled")

#         with cols[4]:
#             if st.button("✏ Edit", key=f"edit_{cid}"):
#                 st.session_state.edit_company_id = cid

#             toggle_label = "Disable" if is_active else "Enable"
#             if st.button(toggle_label, key=f"toggle_{cid}"):
#                 set_company_active(cid, 0 if is_active else 1)
#                 toast("Company status updated")
#                 st.rerun()

#     # ---------------- EDIT COMPANY ----------------
#     if "edit_company_id" in st.session_state:
#         cid = st.session_state.edit_company_id
#         company = [c for c in companies if c[0] == cid][0]

#         st.divider()
#         st.subheader("✏ Edit Company")

#         new_name = st.text_input("Company Name", company[1])
#         new_gst = st.text_input("GST Number", company[2] or "")
#         new_plan = st.selectbox(
#             "Plan",
#             ["free", "pro"],
#             index=0 if company[3] == "free" else 1
#         )

#         if st.button("Save Changes"):
#             update_company(cid, new_name, new_gst, new_plan)
#             toast("Company updated")
#             del st.session_state.edit_company_id
#             st.rerun()

#         if st.button("Cancel"):
#             del st.session_state.edit_company_id
#             st.rerun()

#     st.stop()


# =================================================
# DASHBOARD
# =================================================
st.title("📊 AI Invoice & Expense Dashboard")

# -------------------------------------------------
# Upload Guard
# -------------------------------------------------
if "files_processed" not in st.session_state:
    st.session_state.files_processed = False

uploaded_files = st.file_uploader(
    "Upload Invoice Images or PDFs",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)

# -------------------------------------------------
# Upload + Duplicate Validation
# -------------------------------------------------
if uploaded_files and not st.session_state.files_processed:
    added, skipped = 0, 0

    for file in uploaded_files:
        try:
            with st.spinner(f"Processing {file.name}..."):
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

                insert_invoice(st.session_state.user_id, data)
                added += 1

        except Exception as e:
            st.error(f"{file.name}: {str(e)}")

    st.session_state.files_processed = True

    if added:
        st.success(f"{added} invoice(s) uploaded successfully 🎉")
    if skipped:
        st.warning(f"{skipped} duplicate invoice(s) skipped")

if not uploaded_files:
    st.session_state.files_processed = False

# -------------------------------------------------
# Load Invoices
# -------------------------------------------------
df_invoices = get_invoices(st.session_state.user_id)

# -------------------------------------------------
# Invoice Table
# -------------------------------------------------
st.subheader("🧾 Invoices")

if not df_invoices.empty:
    edited_df = st.data_editor(
        df_invoices,
        use_container_width=True,
        num_rows="fixed"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Changes"):
            for _, row in edited_df.iterrows():
                update_invoice(row["id"], row.to_dict())
            st.success("Invoices updated successfully")

    with col2:
        del_id = st.selectbox("Delete Invoice", df_invoices["id"])
        if st.button("Delete"):
            delete_invoice(del_id)
            st.success("Invoice deleted")
            st.rerun()
else:
    st.info("No invoices uploaded yet.")

# -------------------------------------------------
# GST VALIDATION
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
        gst_df[col] = pd.to_numeric(gst_df[col], errors="coerce").fillna(0)

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
# Monthly Trend
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
    st.bar_chart(df_vendor.set_index("vendor"))

# -------------------------------------------------
# Category Analytics
# -------------------------------------------------
st.subheader("🧩 Category-wise Spend")

df_category = get_category_spend(st.session_state.user_id)
if not df_category.empty:
    st.bar_chart(df_category.set_index("category"))
