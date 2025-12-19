import pandas as pd
from db.invoice_repo import update_invoice

def import_excel_and_sync(uploaded_file):
    df = pd.read_excel(uploaded_file)

    required_cols = {"id", "invoice_number", "subtotal", "gst_percent", "tax"}
    if not required_cols.issubset(df.columns):
        raise ValueError("Invalid Excel format")

    for _, row in df.iterrows():
        update_invoice(row["id"], row.to_dict())
