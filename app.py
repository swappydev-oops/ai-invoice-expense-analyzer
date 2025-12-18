import streamlit as st
import pandas as pd
from PIL import Image
from utils import extract_invoice_details_from_image
import os
from pdf2image import convert_from_bytes

st.set_page_config(page_title="AI Invoice & Expense Analyzer", layout="wide")
st.title("🧾 AI Invoice & Expense Analyzer (v2)")

uploaded_files = st.file_uploader(
    "Upload Invoices (Images or PDFs)",
    type=["png", "jpg", "jpeg", "pdf"],
    accept_multiple_files=True
)

history_file = "invoice_history.csv"
all_data = []

if uploaded_files:
    for file in uploaded_files:
        images = []

        if file.type == "application/pdf":
            images = convert_from_bytes(file.read())
        else:
            images = [Image.open(file)]

        for img in images:
            with st.spinner(f"Processing {file.name}..."):
                try:
                    data = extract_invoice_details_from_image(img)
                    all_data.append(data)
                except Exception as e:
                    st.error(f"{file.name}: {str(e)}")

    if all_data:
        df = pd.DataFrame(all_data)
        st.success("Invoices processed successfully")
        st.dataframe(df)

        # ---------- CSV APPEND ----------
        if os.path.exists(history_file):
            old = pd.read_csv(history_file)
            df = pd.concat([old, df], ignore_index=True)

        df.to_csv(history_file, index=False)

        st.download_button(
            "⬇ Download Full Invoice History",
            df.to_csv(index=False).encode("utf-8"),
            "invoice_history.csv",
            "text/csv"
        )
