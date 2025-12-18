import requests
import re
import io
import base64
from categories import EXPENSE_CATEGORIES

# 🔑 Replace with your OCR.space API key
OCR_API_KEY = "K85063436188957"


def extract_invoice_details_from_image(image):
    """
    Extract invoice details from an invoice image using OCR.space
    Returns structured invoice data as a dictionary
    """

    # ---------- Convert image to Base64 ----------
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    image_base64 = base64.b64encode(buffered.getvalue()).decode()

    payload = {
        "apikey": OCR_API_KEY,
        "base64Image": f"data:image/png;base64,{image_base64}",
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

    # ---------- Error Handling ----------
    if result.get("IsErroredOnProcessing"):
        raise Exception(result.get("ErrorMessage", "OCR processing failed"))

    parsed_results = result.get("ParsedResults")
    if not parsed_results:
        raise Exception("OCR returned no text")

    text = parsed_results[0].get("ParsedText", "")

    # ---------- INVOICE NUMBER ----------
    invoice_match = re.search(
        r"Invoice\s*No[:\s]*([A-Za-z0-9-]+)",
        text,
        re.IGNORECASE
    )
    invoice_number = invoice_match.group(1) if invoice_match else ""

    # ---------- INVOICE DATE (supports text month) ----------
    date_match = re.search(
        r"Invoice\s*Date[:\s]*([0-9]{2}-[A-Za-z]{3}-[0-9]{4})",
        text,
        re.IGNORECASE
    )
    invoice_date = date_match.group(1) if date_match else ""

    # ---------- VENDOR NAME ----------
    vendor_match = re.search(
        r"Vendor\s*Name[:\s]*\n\s*(.+)",
        text,
        re.IGNORECASE
    )
    vendor = vendor_match.group(1).strip() if vendor_match else ""

    # ---------- SUBTOTAL ----------
    subtotal_match = re.search(
        r"Subtotal[:\s]*₹?\s*([0-9,]+)",
        text,
        re.IGNORECASE
    )
    subtotal = subtotal_match.group(1) if subtotal_match else ""

    # ---------- TAX / GST ----------
    tax_match = re.search(
        r"(GST|Tax).*?₹?\s*([0-9,]+)",
        text,
        re.IGNORECASE
    )
    tax = tax_match.group(2) if tax_match else ""

    # ---------- TOTAL AMOUNT ----------
    total_match = re.search(
        r"Total\s*Amount[:\s]*₹?\s*([0-9,]+)",
        text,
        re.IGNORECASE
    )
    total_amount = total_match.group(1) if total_match else ""

    # ---------- CATEGORY LOGIC ----------
    category = "Other"
    if "software" in text.lower():
        category = "Software / Subscriptions"
    elif "maintenance" in text.lower():
        category = "Maintenance"
    elif "travel" in text.lower():
        category = "Travel"

    # ---------- FINAL STRUCTURED DATA ----------
    data = {
        "invoice_number": invoice_number,
        "vendor": vendor,
        "date": invoice_date,
        "total_amount": total_amount,
        "tax": tax,
        "category": category
    }

    return data
