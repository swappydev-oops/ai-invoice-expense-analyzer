def generate_gst_report(df):
    return {
        "invoice_count": int(len(df)),
        "total_taxable": float(df["subtotal"].sum()),
        "total_gst": float(df["tax"].sum()),
        "gst_by_rate": (
            df.groupby("gst_percent")["tax"]
            .sum()
            .to_dict()
        )
    }
