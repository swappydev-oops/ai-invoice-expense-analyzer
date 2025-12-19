import pandas as pd
from io import BytesIO

def export_full_excel(df_invoices, df_gst, df_vendor):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_invoices.to_excel(writer, index=False, sheet_name="Invoices")
        df_gst.to_excel(writer, index=False, sheet_name="Monthly_GST")

        vendor_pivot = pd.pivot_table(
            df_vendor,
            values="total_spend",
            index="vendor",
            aggfunc="sum"
        )
        vendor_pivot.to_excel(writer, sheet_name="Vendor_Pivot")

    output.seek(0)
    return output
