import streamlit as st
import pandas as pd
import time
from PIL import Image
from io import BytesIO
from openpyxl.utils import get_column_letter

from db.db import init_db
from auth.auth import require_login
from db.invoice_repo import (
    insert_invoice,
    get_invoices,
    update_invoice,
    delete_invoice
)
from utils import extract_invoice_details

# -------------------------------------------------
# Safe Toast Helper (works on all Streamlit versions)
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
# File Upload
# -------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload Invoice Images or PDFs",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)

# -------------------------------------------------
# Upload & OCR Processing
# -------------------------------------------------
if uploaded_files:
    for file in uploaded_files:
        try:
            with st.spinner(f"Processing {file.name}..."):
                if file.type == "application/pdf":
                    data = extract_invoice_details(file, "pdf")
                else:
                    image = Image.open(file)
                    data = extract_invoice_details(image, "image")

                data["source_file"] = file.name

                insert_invoice(
                    user_id=st.session_state.user_id,
                    data=data
                )

        except Exception as e:
            st.error(f"{file.name}: {str(e)}")

    show_toast("Invoice(s) uploaded successfully 🎉")
    st.rerun()

# -------------------------------------------------
# Load Invoices from DB (Current User Only)
# -------------------------------------------------
df_db = get_invoices(st.session_state.user_id)

# -------------------------------------------------
# Invoice Management Section
# -------------------------------------------------
st.subheader("📊 Uploaded Invoices")

if not df_db.empty:

    # ---------------- Editable Table ----------------
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
            st.rerun()

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

    # -------------------------------------------------
    # Excel Export (DB → Excel)
    # -------------------------------------------------
    st.subheader("⬇ Download Invoice History")

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_db.drop(columns=["id"]).to_excel(
            writer, index=False, sheet_name="Invoices"
        )
        ws = writer.sheets["Invoices"]

        # Auto column width
        for idx, col in enumerate(df_db.drop(columns=["id"]).columns, 1):
            col_letter = get_column_letter(idx)
            max_len = max(
                df_db[col].astype(str).map(len).max(),
                len(col)
            )
            ws.column_dimensions[col_letter].width = max_len + 3

    output.seek(0)

    st.download_button(
        label="Download Excel",
        data=output,
        file_name="invoice_history.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("No invoices uploaded yet.")
