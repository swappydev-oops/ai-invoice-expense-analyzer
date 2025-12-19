import streamlit as st
import pandas as pd
import time
from PIL import Image

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
from db.user_repo import (
    get_all_users,
    create_user,
    update_user_role,
    delete_user
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
# Init
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
        
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if st.sidebar.button("🛠 Admin Panel"):
    st.session_state.page = "admin"

# -------------------------------------------------
# Admin Panel
# -------------------------------------------------

if st.session_state.page == "admin":
    st.title("🛠 Admin Panel – User Management")

    st.info(
        "Admin Panel is currently open to all users. "
        "Role-based access will be enforced later."
    )

    # -------- CREATE USER --------
    with st.expander("➕ Create New User"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["admin", "user"])
        plan = st.selectbox("Plan", ["free", "pro"])

        if st.button("Create User"):
            try:
                create_user(email, password, role, plan)
                st.success("User created successfully")
                st.rerun()
            except Exception:
                st.error("User already exists or invalid input")

    st.divider()

    # -------- USER TABLE --------
    st.subheader("👥 Users")

    users = get_all_users()

    if not users:
        st.info("No users found")
    else:
        for user_id, email, role, plan, created_at in users:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])

            col1.write(email)
            col2.write(plan)

            new_role = col3.selectbox(
                "Role",
                ["admin", "user"],
                index=0 if role == "admin" else 1,
                key=f"role_{user_id}"
            )

            if new_role != role:
                if col4.button("Update", key=f"update_{user_id}"):
                    update_user_role(user_id, new_role)
                    st.success("Role updated")
                    st.rerun()

            if col5.button("Delete", key=f"delete_{user_id}"):
                delete_user(user_id)
                st.warning("User deleted")
                st.rerun()

    st.divider()

    if st.button("⬅ Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.stop()


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
        show_toast(f"{added} invoice(s) uploaded successfully 🎉")
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
            show_toast("Invoices updated successfully")

    with col2:
        del_id = st.selectbox("Delete Invoice", df_invoices["id"])
        if st.button("Delete"):
            delete_invoice(del_id)
            show_toast("Invoice deleted")
            st.rerun()
else:
    st.info("No invoices uploaded yet.")

# -------------------------------------------------
# GST VALIDATION (FIXED & SAFE)
# -------------------------------------------------
st.subheader("⚠ GST Validation Flags")

if not df_invoices.empty:
    gst_df = df_invoices.copy()

    # ---- FORCE NUMERIC CONVERSION (CRITICAL FIX) ----
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
