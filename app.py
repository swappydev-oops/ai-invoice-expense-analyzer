import streamlit as st
import pandas as pd
from PIL import Image
import os
from io import BytesIO

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
        # -------- CURRENT BATCH --------
        df_new = pd.DataFrame(all_data)

        # -------- LOAD RAW HISTORY --------
        if os.path.exists(HISTORY_FILE):
            df_old = pd.read_csv(HISTORY_FILE)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new.copy()

        # -------- DATA CLEANUP (RAW ONLY) --------
        df_final["date"] = pd.to_datetime(
            df_final["date"], errors="coerce", dayfirst=True
        ).dt.strftime("%Y-%m-%d")

        NUMERIC_COLUMNS = ["subtotal", "tax", "gst_percent", "total_amount"]
        for col in NUMERIC_COLUMNS:
            df_final[col] = pd.to_numeric(df_final[col], errors="coerce")

        CONF_COLS = [c for c in df_final.columns if c.endswith("_conf")]
        for col in CONF_COLS:
            df_final[col] = (df_final[col] * 100).round(0)

        # -------- DEDUPLICATION --------
        df_final = df_final.drop_duplicates(
            subset=["invoice_number", "vendor", "date", "source_file"],
            keep="first"
        )

        # -------- SAVE RAW HISTORY (CSV) --------
        df_final.to_csv(HISTORY_FILE, index=False)

        # -------- UI DISPLAY (CURRENT UPLOAD ONLY) --------
        df_new_display = df_new.rename(columns=DISPLAY_COLUMN_MAPPING)
        st.success(f"{len(df_new_display)} invoices processed successfully")
        st.dataframe(df_new_display, use_container_width=True)

        # -------- EXCEL EXPORT (FORMATTED) --------
        df_final_display = df_final.rename(columns=DISPLAY_COLUMN_MAPPING)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_final_display.to_excel(writer, index=False, sheet_name="Invoices")
            worksheet = writer.sheets["Invoices"]

            # Auto column width
            for idx, col in enumerate(df_final_display.columns, 1):
                max_len = max(
                    df_final_display[col].astype(str).map(len).max(),
                    len(col)
                )
                worksheet.column_dimensions[chr(64 + idx)].width = max_len + 3

            # Formatting rows
            for row in range(2, len(df_final_display) + 2):
                worksheet[f"E{row}"].number_format = "YYYY-MM-DD"
                worksheet[f"G{row}"].number_format = "#,##0"
                worksheet[f"I{row}"].number_format = "#,##0"
                worksheet[f"J{row}"].number_format = "0.00%"
                worksheet[f"L{row}"].number_format = "#,##0"

        output.seek(0)

        st.download_button(
            label="⬇ Download Invoice History (Excel)",
            data=output,
            file_name="invoice_history.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
