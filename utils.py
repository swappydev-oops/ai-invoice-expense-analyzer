import requests
import re
from categories import EXPENSE_CATEGORIES
import io
import base64

API_KEY = "K85063436188957"

def extract_invoice_details_from_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")

    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    payload = {
        "apikey": API_KEY,
        "base64Image": f"data:image/png;base64,{img_base64}",
        "language": "eng",
        "isOverlayRequired": False,
        "OCREngine": 2
    }

    response = requests.post(
        "https://api.ocr.space/parse/image",
        data=payload,
        timeout=30
    )

    result = response.json()

    if result.get("IsErroredOnProcessing"):
        raise Exception(result.get("ErrorMessage"))

    parsed_results = result.get("ParsedResults")
    if not parsed_results:
        raise Exception("OCR returned no text")

    text = parsed_results[0].get("ParsedText", "")

    # ---- Extraction logic ----
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
