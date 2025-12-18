import streamlit as st
import pandas as pd
from PIL import Image
import os

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

        # -------- Load history (RAW, not renamed) --------
        if os.path.exists(HISTORY_FILE):
            df_old = pd.read_csv(HISTORY_FILE)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new

        # -------- Data cleanup (RAW columns only) --------

        # Date normalization
        df_final["date"] = pd.to_datetime(
            df_final["date"], errors="coerce", dayfirst=True
        ).dt.strftime("%Y-%m-%d")

        # Numeric columns
        NUMERIC_COLUMNS = ["subtotal", "tax", "gst_percent", "total_amount"]
        for col in NUMERIC_COLUMNS:
            df_final[col] = pd.to_numeric(df_final[col], errors="coerce")

        # Confidence → percentage
        CONF_COLS = [c for c in df_final.columns if c.endswith("_conf")]
        for col in CONF_COLS:
            df_final[col] = (df_final[col] * 100).round(0)

        # Deduplicate
        df_final = df_final.drop_duplicates(
            subset=["invoice_number", "vendor", "date", "source_file"],
            keep="first"
        )

        # -------- Create DISPLAY dataframe (ONLY ONCE) --------
        df_display = df_final.rename(columns=DISPLAY_COLUMN_MAPPING)

        # Defensive: ensure no duplicate column names
        df_display = df_display.loc[:, ~df_display.columns.duplicated()]

        # -------- Save & Display --------
        st.success("Invoices processed successfully")
        st.dataframe(df_display, use_container_width=True)

        df_display.to_csv(HISTORY_FILE, index=False)

        st.download_button(
            label="⬇ Download Invoice History (CSV)",
            data=df_display.to_csv(index=False).encode("utf-8"),
            file_name="invoice_history.csv",
            mime="text/csv"
        )
