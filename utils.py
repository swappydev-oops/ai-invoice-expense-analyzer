import requests
import re
from categories import EXPENSE_CATEGORIES

API_KEY = "K85063436188957"

def extract_invoice_details_from_image(image):
    import io

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()

    response = requests.post(
        "https://api.ocr.space/parse/image",
        files={"image": img_bytes},
        data={"apikey": API_KEY, "language": "eng"}
    )

    result = response.json()

    parsed_results = result.get("ParsedResults")
    if not parsed_results:
        raise Exception("OCR failed or no text returned")

    text = parsed_results[0].get("ParsedText", "")

    invoice_number = re.search(r"Invoice\s*No[:\s]*([A-Za-z0-9-]+)", text)
    date = re.search(r"Date[:\s]*([0-9/-]+)", text)
    total_amount = re.search(r"Total.*?([0-9,.]+)", text)
    tax = re.search(r"(GST|Tax).*?([0-9,.]+)", text)

    vendor = text.strip().split("\n")[0] if text else ""

    data = {
        "invoice_number": invoice_number.group(1) if invoice_number else "",
        "vendor": vendor,
        "date": date.group(1) if date else "",
        "total_amount": total_amount.group(1) if total_amount else "",
        "tax": tax.group(2) if tax else "",
        "category": EXPENSE_CATEGORIES[0] if total_amount else EXPENSE_CATEGORIES[-1]
    }

    return data
