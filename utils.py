import requests
import re
from categories import EXPENSE_CATEGORIES

API_KEY = "K85063436188957"

def extract_invoice_details_from_image(image):
    import io
    from PIL import Image

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()

    response = requests.post(
        "https://api.ocr.space/parse/image",
        files={"image": img_bytes},
        data={"apikey": API_KEY, "language": "eng"}
    )

    result = response.json()
    text = result.get("ParsedResults")[0].get("ParsedText", "")

    # Simple extraction logic
    invoice_number = re.search(r"Invoice\s*No[:\s]*([A-Za-z0-9-]+)", text)
    date = re.search(r"Date[:\s]*([0-9/-]+)", text)
    total_amount = re.search(r"Total.*?([0-9,.]+)", text)
    vendor_match = text.strip().split("\n")[0] if text else ""

    tax = re.search(r"(GST|Tax).*?([0-9,.]+)", text)

    data = {
        "invoice_number": invoice_number.group(1) if invoice_number else "",
        "vendor": vendor_match,
        "date": date.group(1) if date else "",
        "total_amount": total_amount.group(1) if total_amount else "",
        "tax": tax.group(2) if tax else "",
        "category": ""
    }

    # Basic category rule
    if data["total_amount"] and float(data["total_amount"].replace(",", "")) > 1000:
        data["category"] = EXPENSE_CATEGORIES[0]
    else:
        data["category"] = EXPENSE_CATEGORIES[-1]

    return data
