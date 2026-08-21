import pymupdf
import requests
import json

PDF_PATH = "demo_data/vendor_b_quotation.pdf"

# 1. Extract text from PDF
doc = pymupdf.open(PDF_PATH)
text = "\n".join(page.get_text() for page in doc)

# 2. Send extracted text to local Ollama
prompt = f"""
You are a procurement quotation extraction system.

Extract the quotation information from the text below.

Return ONLY valid JSON with these fields:

{{
    "vendor_name": "",
    "quotation_number": "",
    "product_name": "",
    "quantity": 0,
    "unit_price": 0,
    "delivery_days": 0,
    "warranty_years": 0,
    "payment_terms": "",
    "tax_percentage": 0,
    "additional_charges": 0,
    "grand_total": 0
}}

QUOTATION TEXT:
{text}
"""

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:7b",
        "prompt": prompt,
        "stream": False
    }
)

result = response.json()

print("\n===== AI EXTRACTION =====\n")
print(result["response"])