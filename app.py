import streamlit as st
import pandas as pd
from PIL import Image
import os

from utils import extract_invoice_details

st.set_page_config(
    page_title="AI Invoice & Expense Analyzer",
    layout="wide"
)

st.title("🧾 AI Invoice & Expense Analyzer (v2)")

uploaded_files = st.file_uploader(
    "Upload Invoice Images or PDFs",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)

HISTORY_FILE = "invoice_history.csv"
all_data = []

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

        st.success("Invoices processed successfully")
        st.dataframe(df_new)

        # ---------- Append to CSV History ----------
        if os.path.exists(HISTORY_FILE):
            df_old = pd.read_csv(HISTORY_FILE)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new

        df_final.to_csv(HISTORY_FILE, index=False)

        st.download_button(
            label="⬇ Download Full Invoice History (CSV)",
            data=df_final.to_csv(index=False).encode("utf-8"),
            file_name="invoice_history.csv",
            mime="tex
