import streamlit as st
import pandas as pd
from PIL import Image
import os
from io import BytesIO
from openpyxl.utils import get_column_letter

from utils import extract_invoice_details

# -------------------------------------------------
# Page Configuration
# -------------------------------------------------
st.set_page_config(
    page_title="AI Invoice & Expense Analyzer",
    layout="wide"
)

st.title("🧾 AI Invoice & Expense Analyzer (v2)")

# -------------------------------------------------
# File Upload
# -------------------------------------------------
uploaded_files = st.file_uploader(
    "Upload Invoice Images or PDFs",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)

HISTORY_FILE = "invoice_history.csv"

# -------------------------------------------------
# Display Column Mapping (UI / Excel only)
# -------------------------------------------------
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

# -------------------------------------------------
# Process Uploaded Files
# -------------------------------------------------
if uploaded_files:
    for file in uploaded_files:
        try:
            with st.spinner(f"Processing {file.name}..."):
                if file.type == "application/pdf":
                    record = extract_invoice_details(file, "pdf")
                else:
                    image = Image.open(file)
                    record = extract_invoice_details(image, "image")

                record["source_file"] = file.name
                all_data.append(record)

        except Exception as e:
            st.error(f"{file.name}: {str(e)}")

    if all_data:
        # ---------------- Current Upload ----------------
        df_new = pd.DataFrame(all_data)

        # ---------------- Load Raw History ----------------
        if os.path.exists(HISTORY_FILE):
            df_old = pd.read_csv(HISTORY_FILE)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new.copy()

        # ---------------- Data Cleanup (RAW columns) ----------------

        # Normalize date
        df_final["date"] = pd.to_datetime(
            df_final["date"], errors="coerce", dayfirst=True
        ).dt.strftime("%Y-%m-%d")

        # Numeric conversion
        NUMERIC_COLUMNS = ["subtotal", "tax", "gst_percent", "total_amount"]
        for col in NUMERIC_COLUMNS:
            df_final[col] = pd.to_numeric(df_final[col], errors="coerce")

        # Confidence → percentage
        CONF_COLS = [c for c in df_final.columns if c.endswith("_conf")]
        for col in CONF_COLS:
            df_final[col] = (df_final[col] * 100).round(0)

        # Deduplicate invoices
        df_final = df_final.drop_duplicates(
            subset=["invoice_number", "vendor", "date", "source_file"],
            keep="first"
        )

        # ---------------- Save RAW history (CSV) ----------------
        df_final.to_csv(HISTORY_FILE, index=False)

        # ---------------- UI Display (current batch only) ----------------
        df_new_display = df_new.rename(columns=DISPLAY_COLUMN_MAPPING)
        st.success(f"{len(df_new_display)} invoice(s) processed successfully")
        st.dataframe(df_new_display, use_container_width=True)

        # ---------------- Excel Export (formatted) ----------------
        df_final_display = df_final.rename(columns=DISPLAY_COLUMN_MAPPING)

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_final_display.to_excel(writer, index=False, sheet_name="Invoices")
            ws = writer.sheets["Invoices"]

            # Auto column width (SAFE)
            for idx, col in enumerate(df_final_display.columns, 1):
                col_letter = get_column_letter(idx)
                max_len = int(
                    max(
                        df_final_display[col]
                        .astype(str)
                        .str.len()
                        .fillna(0)
                        .max(),
                        len(col)
                    )
                )
                ws.column_dimensions[col_letter].width = max_len + 3

            # Column formatting
            for row in range(2, len(df_final_display) + 2):
                ws[f"E{row}"].number_format = "YYYY-MM-DD"   # Invoice Date
                ws[f"G{row}"].number_format = "#,##0"        # Subtotal
                ws[f"I{row}"].number_format = "#,##0"        # GST Amount
                ws[f"J{row}"].number_format = "0.00%"        # GST %
                ws[f"L{row}"].number_format = "#,##0"        # Total Amount

        output.seek(0)

        st.download_button(
            label="⬇ Download Invoice History (Excel)",
            data=output,
            file_name="invoice_history.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
