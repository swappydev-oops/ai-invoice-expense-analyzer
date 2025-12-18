import streamlit as st
import pandas as pd
from PIL import Image
import os
from io import BytesIO
from openpyxl.utils import get_column_letter

from utils import extract_invoice_details

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="AI Invoice & Expense Analyzer",
    layout="wide"
)

st.title("🧾 AI Invoice & Expense Analyzer (v2)")

# ---------------- Upload ----------------
uploaded_files = st.file_uploader(
    "Upload Invoice Images or PDFs",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)

HISTORY_FILE = "invoice_history.csv"

# ---------------- Display Header Mapping ----------------
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

all_data = []

# ---------------- Processing ----------------
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
                all_data.append(data)

        except Exception as e:
            st.error(f"{file.name}: {str(e)}")

    if all_data:
        df_new = pd.DataFrame(all_data)

        # -------- Load RAW history --------
        if os.path.exists(HISTORY_FILE):
            df_old = pd.read_csv(HISTORY_FILE)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new.copy()

        # -------- Cleanup (RAW columns only) --------
        df_final["date"] = pd.to_datetime(
            df_final["date"], errors="coerce", dayfirst=True
        ).dt.strftime("%Y-%m-%d")

        NUMERIC_COLUMNS = ["subtotal", "tax", "gst_percent", "total_amount"]
for col in NUMERIC_COLUMNS:
    df_final[col] = pd.to_numeric(df_final[col], errors="coerce")

