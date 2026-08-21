# ProcureAI Backend & Database

FastAPI backend and database engine for the ProcureAI intelligent procurement platform.

---

## Features

- **12 Relational Models**: `users`, `vendors`, `rfqs`, `rfq_items`, `quotations`, `quotation_items`, `vendor_scores`, `anomalies`, `ai_analyses`, `purchase_orders`, `purchase_order_items`, `audit_logs`.
- **Deterministic 0–100 Vendor Scoring**: Fully reproducible, normalized multi-criteria scoring engine with configurable weights for Price, Delivery, Quality, Warranty, Payment terms, and Compliance.
- **Anomaly Detection**: Automated detection of delivery violations, warranty shortfalls, price/total mismatches, unexpected charges, and suspicious pricing.
- **AI Decision Trace & Negotiation Tactics**: Explainable decision engine with pluggable Ollama LLM integration (Qwen 2.5 7B) and deterministic fallback mock.
- **What-If Recalculation**: Instant dynamic re-ranking without requiring LLM inference.
- **Human Approval & Purchase Order Generation**: Converts approved quotations directly to purchase orders with full line items and audit logging.
- **Dual Database Support**: Seamlessly connects to MySQL (`pymysql`) or falls back cleanly to local SQLite (`procureai.db`) for zero-configuration local development.

---

## Tech Stack & Dependencies

- **Python 3.10+ / 3.12**
- **FastAPI** (REST API framework)
- **Uvicorn** (ASGI server)
- **SQLAlchemy 2.0** (ORM & Database layer)
- **PyMySQL & Cryptography** (MySQL drivers)
- **Pydantic v2 & Pydantic Settings** (Data validation & configuration)
- **HTTPX** (Async HTTP client for AI/Ollama communication)

---

## Quickstart & Setup

### 1. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` or edit `backend/.env`:

```env
# Application Settings
PROJECT_NAME="ProcureAI Backend"
API_V1_STR="/api"
DEBUG=True

# MySQL Configuration (Optional: automatically falls back to SQLite if MySQL is offline)
DB_USER=root
DB_PASSWORD=root
DB_HOST=localhost
DB_PORT=3306
DB_NAME=procureai

# Or direct DATABASE_URL:
# DATABASE_URL=mysql+pymysql://root:root@localhost:3306/procureai
DATABASE_URL=sqlite:///./procureai.db

# AI Service Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
USE_MOCK_AI=True
```

### 3. Initialize & Seed Database

```bash
# Initialize tables
python database/init_db.py

# Seed demo dataset (Vendors A, B, C, 500 Laptops RFQ, quotations, and analysis)
python database/seed_data.py
```

### 4. Run the FastAPI Server

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Open your browser to:
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## API Reference Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/vendors` | List all vendors (supports category & search filtering) |
| `POST` | `/api/vendors` | Create a new vendor profile |
| `GET` | `/api/rfqs` | List all RFQs |
| `POST` | `/api/rfqs` | Create a new RFQ with line items |
| `GET` | `/api/rfqs/{id}` | Get RFQ details, quotation counts & analysis status |
| `POST` | `/api/rfqs/{id}/quotations` | Submit/upload vendor quotation for an RFQ |
| `GET` | `/api/rfqs/{id}/quotations` | List all submitted quotations for an RFQ |
| `POST` | `/api/rfqs/{id}/analyze` | Execute anomaly detection, scoring & decision trace |
| `GET` | `/api/rfqs/{id}/analysis` | Fetch full analysis results, scores & trace |
| `GET` | `/api/rfqs/{id}/recommendation` | Fetch top recommendation & summary |
| `POST` | `/api/rfqs/{id}/recalculate` | Dynamic what-if weight recalculation |
| `POST` | `/api/rfqs/{id}/approve` | Human approval & Purchase Order creation |
| `POST` | `/api/purchase-orders` | Create a direct Purchase Order |
| `GET` | `/api/purchase-orders/{id}` | Retrieve Purchase Order details with line items |
| `GET` | `/api/dashboard/stats` | Dashboard statistics & recent activities |

---

## Running Automated Tests

```bash
pytest tests/test_api_endpoints.py -v
```
