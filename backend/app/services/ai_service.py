import json
import logging
from typing import Dict, Any, List, Optional
import httpx
from backend.app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    Service interface for AI and LLM integration.
    Supports local Ollama Qwen 2.5 7B inference with graceful deterministic fallback.
    """

    @classmethod
    async def call_ollama(cls, prompt: str, system_prompt: str = "") -> Optional[str]:
        """Calls local Ollama API if available."""
        if settings.USE_MOCK_AI:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    f"{settings.OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "prompt": prompt,
                        "system": system_prompt,
                        "stream": False,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    return data.get("response", "").strip()
        except Exception as e:
            logger.info(f"Ollama local inference unavailable ({e}), using deterministic AI service fallback.")
        return None

    @classmethod
    def generate_decision_trace(
        cls,
        rfq_title: str,
        rfq_quantity: int,
        target_price: float,
        max_delivery: int,
        min_warranty: int,
        ranked_vendors_data: List[Dict[str, Any]],
        anomalies_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generates structured decision trace explaining strengths, risks, compliance, and trade-offs.
        """
        if not ranked_vendors_data:
            return {
                "recommended_vendor": "None",
                "summary_of_tradeoffs": "No vendor quotations submitted.",
                "vendor_evaluations": [],
            }

        top_vendor = ranked_vendors_data[0]
        evaluations = []

        for v in ranked_vendors_data:
            v_name = v.get("name", f"Vendor {v.get('vendor_id')}")
            v_anomalies = [a for a in anomalies_data if a.get("vendor_id") == v.get("vendor_id")]
            has_crit = any(a.get("severity") == "CRITICAL" for a in v_anomalies)

            strengths = []
            risks = []

            # Strengths
            if v.get("delivery_score", 0) >= 80:
                strengths.append(f"Fast delivery commitment ({v.get('delivery_days')} days <= max {max_delivery} days)")
            if v.get("price_score", 0) >= 80:
                strengths.append(f"Competitive pricing (₹{v.get('unit_price', 0):,.2f} per unit)")
            if v.get("warranty_score", 0) >= 80:
                strengths.append(f"Robust warranty coverage ({v.get('warranty_years')} years)")
            if v.get("payment_score", 0) >= 80:
                strengths.append(f"Favorable payment credit terms ({v.get('payment_terms')})")

            # Risks / Anomalies
            for a in v_anomalies:
                risks.append(f"[{a.get('severity')}] {a.get('message')}")

            if not risks:
                risks.append("No critical compliance or pricing discrepancies detected.")

            compliance_status = "Non-compliant (Critical Risks)" if has_crit else ("Compliant with Warnings" if v_anomalies else "Fully Compliant")
            
            evaluations.append({
                "vendor_id": v.get("vendor_id"),
                "vendor_name": v_name,
                "rank": v.get("rank"),
                "final_score": v.get("final_score"),
                "strengths": strengths or ["Standard market terms provided"],
                "risks": risks,
                "compliance_summary": compliance_status,
                "commercial_terms": f"₹{v.get('unit_price', 0):,.2f}/unit | {v.get('delivery_days')} days | {v.get('warranty_years')} yr warranty | {v.get('payment_terms')}",
            })

        # Summary of tradeoffs
        if len(ranked_vendors_data) >= 2:
            second_vendor = ranked_vendors_data[1]
            tradeoff_text = (
                f"{top_vendor.get('name')} is recommended as Rank 1 with an overall weighted score of {top_vendor.get('final_score')}/100. "
                f"It delivers the optimal trade-off between price (₹{top_vendor.get('unit_price', 0):,.2f}/unit), "
                f"delivery turnaround ({top_vendor.get('delivery_days')} days), and warranty compliance without critical contract risks. "
                f"In comparison, {second_vendor.get('name')} scored {second_vendor.get('final_score')}/100."
            )
        else:
            tradeoff_text = f"{top_vendor.get('name')} is the sole ranked bidder with a score of {top_vendor.get('final_score')}/100."

        return {
            "recommended_vendor": top_vendor.get("name", f"Vendor {top_vendor.get('vendor_id')}"),
            "recommended_vendor_id": top_vendor.get("vendor_id"),
            "summary_of_tradeoffs": tradeoff_text,
            "vendor_evaluations": evaluations,
        }

    @classmethod
    def generate_negotiation_strategy(
        cls,
        ranked_vendors_data: List[Dict[str, Any]],
        target_price: float,
    ) -> str:
        """
        Generates tactical negotiation strategies for procurement officers based on competitive benchmarks.
        """
        if not ranked_vendors_data:
            return "No vendors available for negotiation."

        strategies = []
        top_vendor = ranked_vendors_data[0]
        cheapest_vendor = min(ranked_vendors_data, key=lambda x: x.get("unit_price", float("inf")))

        for v in ranked_vendors_data:
            v_name = v.get("name", f"Vendor {v.get('vendor_id')}")
            unit_price = v.get("unit_price", 0)
            
            tactics = []
            if unit_price > cheapest_vendor.get("unit_price", 0):
                diff = unit_price - cheapest_vendor.get("unit_price", 0)
                tactics.append(
                    f"Leverage lowest benchmark quote (₹{cheapest_vendor.get('unit_price', 0):,.2f}) to counter ₹{diff:,.2f} price premium."
                )
            
            if v.get("delivery_days", 0) > 15:
                tactics.append(
                    f"Demand delivery commitment reduction from {v.get('delivery_days')} days to <= 15 days or request 2% late-penalty clause."
                )
            
            if "30" in str(v.get("payment_terms", "")):
                tactics.append("Negotiate payment terms extension from Net 30 to Net 45 days to optimize working capital.")

            if not tactics:
                tactics.append(f"Negotiate volume rebate of 3-5% based on overall order size of {target_price:,.0f} budget.")

            strategies.append(f"### {v_name} (Rank #{v.get('rank', 1)}):\n" + "\n".join(f"- {t}" for t in tactics))

        return "\n\n".join(strategies)
