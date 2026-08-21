"""
AI Decision Explanation module using Qwen 2.5 7B.
"""

import json
import logging
from typing import Dict, Any, List, Optional
import requests

from ai.config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
from ai.extraction import clean_json_response

logger = logging.getLogger(__name__)


def generate_fallback_explanation(
    ranked_vendors: List[Dict[str, Any]],
    anomalies_by_vendor: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Generates a deterministic factual fallback explanation without calling the LLM.
    """
    if not ranked_vendors:
        return {
            "recommendation_explanation": "No vendors available to evaluate.",
            "key_reasons": [],
            "major_risks": [],
            "trade_offs": [],
        }

    winner = ranked_vendors[0]
    w_name = winner.get("vendor_name", "Winning Vendor")
    w_score = winner.get("final_score", 0.0)

    reasons = [
        f"{w_name} achieved the highest overall score of {w_score:.2f}/100.",
        f"Delivered strong component scores: Price ({winner['component_scores'].get('price', 0)}), "
        f"Delivery ({winner['component_scores'].get('delivery', 0)}), "
        f"Quality ({winner['component_scores'].get('quality', 0)}).",
    ]

    risks = []
    for v in ranked_vendors:
        v_name = v.get("vendor_name", "Vendor")
        v_anomalies = anomalies_by_vendor.get(v_name, [])
        for a in v_anomalies:
            risks.append(f"{v_name}: [{a.get('anomaly_type')}] {a.get('message')}")

    trade_offs = []
    if len(ranked_vendors) > 1:
        runner_up = ranked_vendors[1]
        trade_offs.append(
            f"Trade-off between {w_name} (Score: {w_score:.2f}) and {runner_up.get('vendor_name')} "
            f"(Score: {runner_up.get('final_score'):.2f})."
        )

    explanation_text = (
        f"Based on deterministic multi-criteria scoring, {w_name} is recommended as the optimal vendor "
        f"with a score of {w_score:.2f}/100."
    )

    return {
        "recommendation_explanation": explanation_text,
        "key_reasons": reasons,
        "major_risks": risks if risks else ["No critical risk flags detected."],
        "trade_offs": trade_offs if trade_offs else ["No major commercial trade-offs required."],
    }


def generate_decision_explanation(
    ranked_vendors: List[Dict[str, Any]],
    matching_results_by_vendor: Dict[str, List[Dict[str, Any]]],
    anomalies_by_vendor: Dict[str, List[Dict[str, Any]]],
    ollama_url: str = OLLAMA_URL,
    model: str = OLLAMA_MODEL,
    timeout: float = OLLAMA_TIMEOUT,
) -> Dict[str, Any]:
    """
    Generates a natural-language recommendation explanation using Qwen 2.5 7B.

    Strictly factual: The LLM is supplied with exact calculated results and must
    not invent external facts, prices, or rankings.
    """
    if not ranked_vendors:
        return generate_fallback_explanation(ranked_vendors, anomalies_by_vendor)

    # Construct concise factual summary payload for LLM prompt
    facts_summary = {
        "ranked_vendors": ranked_vendors,
        "requirement_matching": matching_results_by_vendor,
        "detected_anomalies": anomalies_by_vendor,
    }

    prompt = f"""You are a procurement intelligence explanation model.
Below are the EXACT calculated results, scores, requirement matches, and anomalies for evaluated vendor quotations.

STRICT INSTRUCTIONS:
1. Base your explanation strictly on the provided factual data.
2. DO NOT invent prices, dates, vendors, or features not present in the data.
3. Return ONLY valid JSON with this exact structure:

{{
    "recommendation_explanation": "Detailed summary explaining why the recommended vendor was selected.",
    "key_reasons": [
        "First key reason based on factual scores/metrics",
        "Second key reason"
    ],
    "major_risks": [
        "Specific risk or anomaly identified for vendors"
    ],
    "trade_offs": [
        "Trade-offs evaluated between vendors (e.g. price vs delivery vs warranty)"
    ]
}}

FACTUAL EVALUATION DATA:
{json.dumps(facts_summary, indent=2)}
"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }

    try:
        response = requests.post(
            f"{ollama_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        raw_text = response.json().get("response", "")
        cleaned_json = clean_json_response(raw_text)

        parsed_data = json.loads(cleaned_json)
        if isinstance(parsed_data, dict) and "recommendation_explanation" in parsed_data:
            return {
                "recommendation_explanation": str(parsed_data.get("recommendation_explanation", "")),
                "key_reasons": parsed_data.get("key_reasons", []),
                "major_risks": parsed_data.get("major_risks", []),
                "trade_offs": parsed_data.get("trade_offs", []),
            }

    except Exception as e:
        logger.warning(f"Ollama explanation call failed or returned unparseable JSON ({e}). Using factual fallback.")

    return generate_fallback_explanation(ranked_vendors, anomalies_by_vendor)
