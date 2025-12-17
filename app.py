import streamlit as st
import pandas as pd
from PIL import Image
from utils import extract_invoice_details_from_image

st.set_page_config(page_title="AI Invoice & Expense Analyzer", layout="centered")

st.title("🧾 AI Invoice & Expense Analyzer for MSMEs")

uploaded_file = st.file_uploader(
    "Upload Invoice Image",
    type=["png", "jpg", "jpeg"]
)

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Invoice", use_column_width=True)

    with st.spinner("Analyzing invoice using AI..."):
        try:
            data = extract_invoice_details_from_image(image)

            df = pd.DataFrame([data])
            st.success("Invoice extracted successfully")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇ Download Excel",
                csv,
                "invoice_expenses.csv",
                "text/csv"
            )

        except Exception as e:
            st.error("Failed to extract invoice data. Please upload a clear image.")
