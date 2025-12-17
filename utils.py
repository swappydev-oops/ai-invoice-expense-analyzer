def extract_invoice_details_from_image(image: Image.Image):
    model = genai.GenerativeModel("gemini-1.5-flash")
    genai.configure(api_key=st.secrets["AIzaSyBILsz7OLnwsFgvPOgumnjb74xF1aTGi24"])

    prompt = f"""
    You are an API.

    Read the invoice image and return ONLY valid JSON.
    No explanation.
    No text.
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

    # Clean markdown if any
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    return json.loads(raw_text)
