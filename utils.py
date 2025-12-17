import google.generativeai as genai
from categories import EXPENSE_CATEGORIES
from PIL import Image
import json

genai.configure(api_key="AIzaSyBILsz7OLnwsFgvPOgumnjb74xF1aTGi24")

def extract_invoice_details_from_image(image: Image.Image):
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
    You are an accounting assistant.

    Extract invoice details from the image.
    Return ONLY valid JSON with these keys:
    invoice_number
    vendor
    date
    total_amount
    tax
    category

    Category must be one of:
    {EXPENSE_CATEGORIES}
    """

    response = model.generate_content(
        [prompt, image],
        generation_config={"temperature": 0}
    )

    text = response.text.strip()

    # Remove markdown if Gemini adds it
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    return json.loads(text)
