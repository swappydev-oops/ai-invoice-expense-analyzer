import google.generativeai as genai
from categories import EXPENSE_CATEGORIES
import json

genai.configure(api_key="AIzaSyBILsz7OLnwsFgvPOgumnjb74xF1aTGi24")

def extract_invoice_details_from_image(image):
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
    You are an API.

    Read the invoice image and return ONLY valid JSON.
    No explanation.
    No markdown.

    JSON format (ALL keys mandatory):
    {{
      "invoice_number": "",
      "vendor": "",
      "date": "",
      "total_amount": "",
      "tax": "",
      "category": ""
    }}

    Category must be one of:
    {EXPENSE_CATEGORIES}
    """

    response = model.generate_content(
        [prompt, image],
        generation_config={"temperature": 0}
    )

    raw_text = response.text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    return json.loads(raw_text)
