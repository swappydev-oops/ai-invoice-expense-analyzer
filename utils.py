import requests
import re
import io
import base64
import datetime
from categories import EXPENSE_CATEGORIES

OCR_API_KEY = "K85063436188957"


def normalize_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, "%d-%b-%Y").strftime("%Y-%m-%d")
    except Exception:
        return ""


def calculate_gst_percentage(subtotal, tax):
    try:
        subtotal = float(subtotal.replace(",", ""))
        tax = float(tax.replace(",", ""))
        return round((tax / subtotal) * 100, 2)
    except Exception:
        return 0


def confidence(found: bool):
    return round(0.95 if found else 0.3, 2)


def call_ocr_space(payload, files=None):
    response = requests.post(
        "https://api.ocr.space/parse/image",
        data=payload,
        files=files,
        timeout=60
    )
    return response.json()


def extract_invoice_details(file, file_type):
    """
    file_type: 'image' or 'pdf'
    """

    # ---------- OCR CALL ----------
    if file_type == "image":
        buffer = io.BytesIO()
        file.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        payload = {
            "apikey": OCR_API_KEY,
            "base64Image": f"data:image/png;base64,{img_base64}",
            "language": "eng",
            "OCREngine": 2
        }

        result = call_ocr_space(payload)

    else:  # PDF
        payload = {
            "apikey": OCR_API_KEY,
            "language": "eng",
            "OCREngine": 2
        }

        result = call_ocr_space(
            payload,
            files={"file": file}
        )

    # ---------- ERROR HANDLING ----------
    if result.get("IsErroredOnProcessing"):
        raise Exception(result.get("ErrorMessage", "OCR failed"))

    parsed = result.get("ParsedResults")
    if not parsed:
        raise Exception("OCR returned no text")

    text = parsed[0].get("ParsedText", "")

    # ---------- FIELD EXTRACTION ----------
    invoice_no = re.search(r"Invoice\s*No[:\s]*([A-Za-z0-9-]+)", text, re.I)
    date_raw = re.search(r"Invoice\s*Date[:\s]*([0-9]{2}-[A-Za-z]{3}-[0-9]{4})", text, re.I)
    vendor = re.search(r"Vendor\s*Name[:\s]*\n\s*(.+)", text, re.I)
    subtotal = re.search(r"Subtotal[:\s]*₹?\s*([0-9,]+)", text, re.I)
    tax = re.search(r"(GST|Tax).*?₹?\s*([0-9,]+)", text, re.I)
    total = re.search(r"Total\s*Amount[:\s]*₹?\s*([0-9,]+)", text, re.I)

    subtotal_val = subtotal.group(1) if subtotal else ""
    tax_val = tax.group(2) if tax else ""

    gst_percent = calculate_gst_percentage(subtotal_val, tax_val)

    category = "Other"
    if "software" in text.lower():
        category = "Software / Subscriptions"
    elif "maintenance" in text.lower():
        category = "Maintenance"
    elif "travel" in text.lower():
        category = "Travel"

    return {
        "invoice_number": invoice_no.group(1) if invoice_no else "",
        "invoice_number_conf": confidence(bool(invoice_no)),

        "vendor": vendor.group(1).strip() if vendor else "",
        "vendor_conf": confidence(bool(vendor)),

        "date": normalize_date(date_raw.group(1)) if date_raw else "",
        "date_conf": confidence(bool(date_raw)),

        "subtotal": subtotal_val,
        "subtotal_conf": confidence(bool(subtotal)),

        "tax": tax_val,
        "gst_percent": gst_percent,
        "tax_conf": confidence(bool(tax)),

        "total_amount": total.group(1) if total else "",
        "total_conf": confidence(bool(total)),

        "category": category
    }
