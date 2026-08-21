# ProcureAI — Master Specification

## 1. Objective

Build an AI-powered procurement intelligence system that helps organizations analyze vendor quotations, detect risks and anomalies, rank vendors according to procurement priorities, explain recommendations, and generate a purchase order after human approval.

## 2. Core Demo Workflow

RFQ Creation
→ Upload Vendor Quotations
→ PDF/Excel Extraction
→ Structured Quotation JSON
→ Requirement Validation
→ Anomaly Detection
→ Deterministic Vendor Scoring
→ Vendor Ranking
→ AI Decision Explanation
→ What-if Analysis
→ Human Approval
→ Purchase Order

## 3. Technology Stack

Frontend:
- React
- TypeScript
- Tailwind CSS
- Recharts

Backend:
- Python
- FastAPI
- SQLAlchemy
- Pydantic

Database:
- MySQL

AI:
- Ollama
- Qwen 2.5 7B
- Local inference

Document Processing:
- PyMuPDF
- openpyxl / pandas

Architecture:
- Modular monolith
- REST APIs
- No microservices
- No LangChain
- No LangGraph

## 4. AI Responsibilities

LLM:
- Extract quotation information from unstructured text
- Understand payment/warranty/commercial terms
- Generate decision explanations
- Generate negotiation suggestions

Python:
- Validate extracted data
- Calculate totals
- Match RFQ requirements
- Detect anomalies
- Calculate vendor scores
- Rank vendors

The LLM must NEVER be the sole authority for financial calculations or vendor ranking.

## 5. Quotation JSON

{
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
}

## 6. RFQ

Example:

500 Business Laptops

Requirements:
- Intel i7 or equivalent
- RAM >= 16 GB
- Storage >= 512 GB SSD
- Warranty >= 3 years
- Delivery <= 15 days
- Target price = ₹50,000/unit

Default weights:
- Price: 30%
- Delivery: 25%
- Quality: 20%
- Warranty: 10%
- Payment: 10%
- Compliance: 5%

Weights must be configurable.

## 7. Vendor Scoring

Final score:

Price × weight
+ Delivery × weight
+ Quality × weight
+ Warranty × weight
+ Payment × weight
+ Compliance × weight

Normalize component scores to 0–100 before applying weights.

The scoring engine must be deterministic and reproducible.

## 8. Anomaly Detection

Detect:
- Delivery violations
- Warranty violations
- Price/total mismatch
- Tax inconsistencies
- Unexpected additional charges
- Missing fields
- Suspicious pricing

Example:

Expected delivery <= 15 days
Vendor quotation = 25 days

→ DELIVERY_VIOLATION
→ CRITICAL

## 9. AI Decision Trace

The system must explain:
- Which requirements each vendor satisfies
- Which requirements each vendor violates
- Price trade-offs
- Delivery trade-offs
- Warranty/payment differences
- Why the recommended vendor was selected

The explanation must be based on structured calculated results.

## 10. What-if Analysis

Allow procurement managers to modify scoring weights.

Example:

Price:
30% → 50%

The backend recalculates vendor scores and rankings.

No LLM is required for recalculation.

## 11. Demo Vendors

Vendor A:
- ₹52,000/unit
- 10 days
- 3 years warranty
- 30-day payment

Vendor B:
- ₹48,500/unit
- 25 days
- 5 years warranty
- 15-day payment
- Deliberate grand-total mismatch

Vendor C:
- ₹49,800/unit
- 12 days
- 3 years warranty
- 45-day payment

Expected story:
B is cheapest but risky.
A is reliable but expensive.
C provides the best overall trade-off.

## 12. API

GET  /api/vendors
POST /api/vendors

GET  /api/rfqs
POST /api/rfqs
GET  /api/rfqs/{id}

POST /api/rfqs/{id}/quotations
GET  /api/rfqs/{id}/quotations

POST /api/rfqs/{id}/analyze
GET  /api/rfqs/{id}/analysis

GET  /api/rfqs/{id}/recommendation
POST /api/rfqs/{id}/recalculate

POST /api/rfqs/{id}/approve

POST /api/purchase-orders
GET  /api/purchase-orders/{id}

GET /api/dashboard/stats

## 13. Folder Ownership

AI:
ai/

Frontend:
frontend/

Backend + Database:
backend/
database/

Documents + Testing:
document_processing/
demo_data/
tests/

## 14. Important Rules

Do not:
- Build microservices
- Build Kubernetes infrastructure
- Add LangChain/LangGraph
- Build mobile apps
- Build full accounting
- Build real payment processing
- Build unnecessary ERP modules
- Hardcode the final vendor recommendation

Prioritize:
1. Working quotation analysis
2. Anomaly detection
3. Deterministic scoring
4. Explainable recommendation
5. What-if analysis
6. Purchase order generation
7. UI polish