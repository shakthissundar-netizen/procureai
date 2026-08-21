import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from database.seed_data import seed_demo_data

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure clean database before testing."""
    seed_demo_data()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "ProcureAI API"
    assert data["status"] == "online"


def test_get_vendors():
    response = client.get("/api/vendors")
    assert response.status_code == 200
    vendors = response.json()
    assert len(vendors) >= 3
    names = [v["name"] for v in vendors]
    assert "TechCorp Solutions" in names
    assert "BudgetHardware Ltd" in names
    assert "PrimeTech Enterprises" in names


def test_create_vendor():
    payload = {
        "name": "Global Supplies Co",
        "email": "contact@globalsupplies.com",
        "phone": "+91 99887 66554",
        "company": "Global Supplies International",
        "category": "Office Equipment",
        "rating": 4.2,
    }
    response = client.post("/api/vendors", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert "id" in data


def test_get_rfqs():
    response = client.get("/api/rfqs")
    assert response.status_code == 200
    rfqs = response.json()
    assert len(rfqs) >= 1
    assert rfqs[0]["rfq_number"] == "RFQ-2026-LAPTOP-500"


def test_create_rfq():
    payload = {
        "title": "200 Ergonomic Office Chairs",
        "description": "Ergonomic mesh chairs with lumbar support and 3D armrests.",
        "quantity": 200,
        "target_unit_price": 12000.0,
        "max_delivery_days": 10,
        "min_warranty_years": 2,
        "created_by": "Facility Head",
        "items": [
            {
                "product_name": "Executive Ergonomic Mesh Chair Pro",
                "description": "High back mesh, synchro-tilt mechanism",
                "quantity": 200,
            }
        ],
    }
    response = client.post("/api/rfqs", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["quantity"] == 200
    assert len(data["items"]) == 1


def test_get_rfq_details():
    response = client.get("/api/rfqs/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["quotation_count"] == 3
    assert data["has_analysis"] is True


def test_quotations_for_rfq():
    response = client.get("/api/rfqs/1/quotations")
    assert response.status_code == 200
    quotations = response.json()
    assert len(quotations) == 3
    for q in quotations:
        assert "vendor" in q
        assert len(q["items"]) > 0


def test_submit_new_quotation():
    payload = {
        "rfq_id": 1,
        "vendor_id": 1,
        "quotation_number": "QUOT-TC-REVISED-002",
        "file_name": "Revised_TechCorp_Bid.pdf",
        "delivery_days": 8,
        "warranty_years": 3,
        "payment_terms": "Net 30 Days",
        "tax_amount": 4500000.0,
        "additional_charges": 0.0,
        "grand_total": 29500000.0,
        "extraction_confidence": 0.99,
        "items": [
            {
                "product_name": "Dell Latitude 5440 Special Edition",
                "quantity": 500,
                "unit_price": 50000.0,
                "total_price": 25000000.0,
            }
        ],
    }
    response = client.post("/api/rfqs/1/quotations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["quotation_number"] == "QUOT-TC-REVISED-002"


def test_analyze_rfq():
    response = client.post("/api/rfqs/1/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["rfq_id"] == 1
    assert len(data["scores"]) >= 3
    assert len(data["anomalies"]) > 0

    # Verify anomalies detected on Vendor B (id 2)
    vendor_b_anomalies = [a for a in data["anomalies"] if a["vendor_id"] == 2]
    anomaly_types = [a["type"] for a in vendor_b_anomalies]
    assert "DELIVERY_VIOLATION" in anomaly_types
    assert "TOTAL_MISMATCH" in anomaly_types

    # Verify recommendation
    assert data["recommended_vendor"] is not None
    assert "decision_trace" in data
    assert "negotiation_strategy" in data


def test_get_analysis_and_recommendation():
    analysis_resp = client.get("/api/rfqs/1/analysis")
    assert analysis_resp.status_code == 200
    assert analysis_resp.json()["rfq_id"] == 1

    rec_resp = client.get("/api/rfqs/1/recommendation")
    assert rec_resp.status_code == 200
    assert rec_resp.json()["recommended_vendor"] is not None


def test_what_if_recalculate():
    # Recalculate giving 70% weight to price
    recalc_payload = {
        "weights": {
            "price_weight": 0.70,
            "delivery_weight": 0.10,
            "quality_weight": 0.10,
            "warranty_weight": 0.05,
            "payment_weight": 0.05,
            "compliance_weight": 0.00,
        }
    }
    response = client.post("/api/rfqs/1/recalculate", json=recalc_payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["scores"]) == 3
    # Check that rank 1 exists
    ranks = [s["rank"] for s in data["scores"]]
    assert 1 in ranks


def test_approve_rfq_and_generate_po():
    approve_payload = {
        "notes": "Approved following automated AI risk evaluation.",
    }
    response = client.post("/api/rfqs/1/approve", json=approve_payload)
    assert response.status_code == 201
    po = response.json()
    assert "po_number" in po
    assert po["status"] == "APPROVED"
    assert po["total"] > 0
    assert len(po["items"]) > 0

    # Verify RFQ status updated to APPROVED
    rfq_resp = client.get("/api/rfqs/1")
    assert rfq_resp.json()["status"] == "APPROVED"


def test_direct_purchase_order_endpoints():
    po_payload = {
        "rfq_id": 1,
        "vendor_id": 3,
        "status": "DRAFT",
        "subtotal": 500000.0,
        "tax": 90000.0,
        "total": 590000.0,
        "delivery_terms": "10 days",
        "payment_terms": "Net 30",
        "items": [
            {
                "product_name": "Server Rack Unit 42U",
                "quantity": 2,
                "unit_price": 250000.0,
                "total_price": 500000.0,
            }
        ],
    }
    create_resp = client.post("/api/purchase-orders", json=po_payload)
    assert create_resp.status_code == 201
    po_data = create_resp.json()
    po_id = po_data["id"]

    get_resp = client.get(f"/api/purchase-orders/{po_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == po_id
    assert len(get_resp.json()["items"]) == 1


def test_dashboard_stats():
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_rfqs"] >= 1
    assert data["total_vendors"] >= 3
    assert data["total_quotations"] >= 3
    assert "recent_rfqs" in data
    assert "recent_anomalies" in data


def test_404_handling():
    response = client.get("/api/rfqs/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_validation_error_handling():
    # Sending missing required fields
    response = client.post("/api/vendors", json={"category": "Invalid"})
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "Validation Error"
