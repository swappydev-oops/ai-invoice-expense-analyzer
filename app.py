import streamlit as st
import pandas as pd
from PIL import image
from utils import extract_invoice_details_from_image

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
        st.error("AI response could not be parsed.")
        st.code(str(e))
