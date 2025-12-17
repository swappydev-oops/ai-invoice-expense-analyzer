import streamlit as st
import pandas as pd
from PIL import Image
import json
from utils import extract_text_from_image, extract_invoice_details

st.set_page_config(page_title="AI Invoice & Expense Analyzer", layout="centered")

st.title("🧾 AI Invoice & Expense Analyzer for MSMEs")

uploaded_file = st.file_uploader("Upload Invoice (Image)", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Invoice", use_column_width=True)

    with st.spinner("Extracting invoice data using AI..."):
        text = extract_text_from_image(image)
        ai_response = extract_invoice_details(text)

    try:
        data = json.loads(ai_response)
        df = pd.DataFrame([data])

        st.success("Invoice data extracted successfully")
        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇ Download Excel",
            csv,
            "invoice_expenses.csv",
            "text/csv"
        )

    except Exception as e:
        st.error("Failed to extract structured data. Please upload a clear invoice.")
