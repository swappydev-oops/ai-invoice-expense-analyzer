import pytesseract
from PIL import Image
import google.generativeai as genai
import re
from categories import EXPENSE_CATEGORIES

genai.configure(api_key="AIzaSyBILsz7OLnwsFgvPOgumnjb74xF1aTGi24")

def extract_text_from_image(image):
    return pytesseract.image_to_string(image)

def extract_invoice_details(text):
    model = genai.GenerativeModel("gemini-pro")

    prompt = f"""
    Extract invoice details from the text below.
    Return JSON with keys:
    invoice_number, vendor, date, total_amount, tax, category

    Categories: {EXPENSE_CATEGORIES}

    Text:
    {text}
    """

    response = model.generate_content(prompt)
    return response.text
