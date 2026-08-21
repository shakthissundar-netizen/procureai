"""
Quotation extraction service using PyMuPDF and Ollama (Qwen 2.5 7B).
"""

import json
import re
import logging
from typing import Dict, Any, Union, Optional
import requests
import pymupdf  # PyMuPDF

from ai.config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

logger = logging.getLogger(__name__)

# Mandatory field set for structured quotation JSON
REQUIRED_FIELDS = [
    "vendor_name",
    "quotation_number",
    "product_name",
    "quantity",
    "unit_price",
    "delivery_days",
    "warranty_years",
    "payment_terms",
    "tax_percentage",
    "additional_charges",
    "grand_total",
]

DEFAULT_QUOTATION_TEMPLATE: Dict[str, Any] = {
    "vendor_name": "",
    "quotation_number": "",
    "product_name": "",
    "quantity": 0,
    "unit_price": 0.0,
    "delivery_days": 0,
    "warranty_years": 0.0,
    "payment_terms": "",
    "tax_percentage": 0.0,
    "additional_charges": 0.0,
    "grand_total": 0.0,
}


def extract_text_from_pdf(pdf_source: Union[str, bytes]) -> str:
    """
    Extracts raw text content from a PDF file path or PDF binary bytes using PyMuPDF.
    """
    text_content = []
    try:
        if isinstance(pdf_source, bytes):
            doc = pymupdf.open(stream=pdf_source, filetype="pdf")
        else:
            doc = pymupdf.open(pdf_source)

        for page in doc:
            page_text = page.get_text()
            if page_text:
                text_content.append(page_text)

        doc.close()
    except Exception as e:
        logger.error(f"Error reading PDF source: {e}")
        raise RuntimeError(f"Failed to extract text from PDF: {e}")

    return "\n".join(text_content).strip()


def clean_json_response(raw_text: str) -> str:
    """
    Cleans raw response from LLM to isolate valid JSON block.
    Strips markdown code blocks, backticks, and extraneous commentary.
    """
    if not raw_text:
        return "{}"

    text = raw_text.strip()

    # Match ```json ... ``` or ``` ... ```
    code_block_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()

    # Fallback to finding first '{' and last '}'
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx : end_idx + 1].strip()

    return text


def parse_llm_json(raw_response: str) -> Dict[str, Any]:
    """
    Safely parses JSON from LLM response with multiple fallback recovery techniques.
    """
    cleaned = clean_json_response(raw_response)

    # 1. Direct JSON attempt
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 2. Attempt fixing common LLM trailing comma issues
    try:
        sanitized = re.sub(r",\s*([\}\]])", r"\1", cleaned)
        data = json.loads(sanitized)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 3. Attempt single quote replacement
    try:
        sanitized = cleaned.replace("'", '"')
        data = json.loads(sanitized)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    logger.warning("Could not parse LLM output as JSON; returning default template.")
    return DEFAULT_QUOTATION_TEMPLATE.copy()


def extract_quotation_data(
    quotation_text: str,
    ollama_url: str = OLLAMA_URL,
    model: str = OLLAMA_MODEL,
    timeout: float = OLLAMA_TIMEOUT,
) -> Dict[str, Any]:
    """
    Extracts structured quotation fields from text using Ollama (Qwen 2.5 7B).

    Guarantees returning a dictionary containing all required fields.
    """
    if not quotation_text or not quotation_text.strip():
        logger.warning("Empty quotation text provided for extraction.")
        result = DEFAULT_QUOTATION_TEMPLATE.copy()
        result["_error"] = "Empty quotation text provided"
        return result

    prompt = f"""You are a professional procurement data extraction assistant.
Extract quotation information from the text below.

You MUST return ONLY valid JSON matching this exact schema:

{{
    "vendor_name": "Vendor Name string",
    "quotation_number": "Quotation reference string",
    "product_name": "Product description",
    "quantity": 0,
    "unit_price": 0.0,
    "delivery_days": 0,
    "warranty_years": 0.0,
    "payment_terms": "Payment terms description",
    "tax_percentage": 0.0,
    "additional_charges": 0.0,
    "grand_total": 0.0
}}

Rules:
1. All monetary values must be raw numbers without currency symbols (e.g. 50000 instead of ₹50,000).
2. Tax percentage must be a number (e.g. 18 for 18%).
3. Delivery days must be an integer (e.g. 15).
4. Warranty years must be a number (e.g. 3 or 0.5).
5. Do NOT include markdown text outside the JSON object. Output strictly valid JSON.

QUOTATION TEXT:
{quotation_text}
"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }

    try:
        response = requests.post(
            f"{ollama_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        resp_data = response.json()
        raw_llm_text = resp_data.get("response", "")

        extracted_dict = parse_llm_json(raw_llm_text)

        # Merge extracted dictionary into default template to guarantee all fields exist
        final_dict = DEFAULT_QUOTATION_TEMPLATE.copy()

        for key in REQUIRED_FIELDS:
            if key in extracted_dict and extracted_dict[key] is not None:
                final_dict[key] = extracted_dict[key]

        return final_dict

    except requests.exceptions.RequestException as req_err:
        logger.error(f"Ollama connection error: {req_err}")
        fallback = DEFAULT_QUOTATION_TEMPLATE.copy()
        fallback["_error"] = f"Ollama service error: {str(req_err)}"
        return fallback
    except Exception as err:
        logger.error(f"Unexpected error during extraction: {err}")
        fallback = DEFAULT_QUOTATION_TEMPLATE.copy()
        fallback["_error"] = f"Unexpected extraction error: {str(err)}"
        return fallback
