import sys
import os
import json

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.vendor import Vendor
from backend.app.models.rfq import RFQ, RFQItem
from backend.app.models.quotation import Quotation, QuotationItem
from backend.app.services.analysis_service import AnalysisService
from database.init_db import init_db


def seed_demo_data():
    # Initialize / reset tables
    init_db(drop_first=True)

    db = SessionLocal()
    try:
        print("Seeding demo data...")

        # 1. Seed Users
        user = User(
            name="Priya Sharma",
            email="priya.sharma@procureai.internal",
            role="lead_procurement_manager",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created demo user: {user.name} ({user.email})")

        # 2. Seed Demo Vendors (A, B, C)
        vendor_a = Vendor(
            name="TechCorp Solutions",
            email="sales@techcorp-solutions.com",
            phone="+91 98765 43210",
            company="TechCorp Solutions Pvt Ltd",
            category="IT Hardware & Infrastructure",
            rating=4.8,
        )
        vendor_b = Vendor(
            name="BudgetHardware Ltd",
            email="deals@budgethardware.com",
            phone="+91 98111 22334",
            company="BudgetHardware Distribution Ltd",
            category="IT Hardware & Peripherals",
            rating=3.9,
        )
        vendor_c = Vendor(
            name="PrimeTech Enterprises",
            email="enterprise@primetech.in",
            phone="+91 98450 11223",
            company="PrimeTech Enterprise Systems",
            category="Enterprise Hardware & OEM",
            rating=4.6,
        )
        db.add_all([vendor_a, vendor_b, vendor_c])
        db.commit()
        db.refresh(vendor_a)
        db.refresh(vendor_b)
        db.refresh(vendor_c)
        print("Created Vendors: Vendor A, Vendor B, Vendor C")

        # 3. Seed Demo RFQ (500 Business Laptops)
        rfq = RFQ(
            rfq_number="RFQ-2026-LAPTOP-500",
            title="Procurement of 500 Enterprise Business Laptops",
            description=(
                "Requirement for 500 high-performance business laptops for engineering and sales team rollout. "
                "Must meet enterprise durability standards, TPM 2.0 security, and on-site warranty."
            ),
            quantity=500,
            status="OPEN",
            target_unit_price=50000.0,
            max_delivery_days=15,
            min_warranty_years=3,
            created_by=user.name,
        )
        db.add(rfq)
        db.flush()

        specs_json = json.dumps({
            "processor": "Intel Core i7 13th Gen or AMD Ryzen 7 equivalent",
            "ram": ">= 16 GB DDR5",
            "storage": ">= 512 GB NVMe SSD",
            "display": "14-inch FHD (1920x1080) Anti-glare IPS",
            "os": "Windows 11 Pro OEM",
            "ports": "Thunderbolt 4 / USB-C, HDMI 2.1, USB-A 3.2",
            "security": "TPM 2.0, Fingerprint reader, Webcam privacy shutter",
        })

        rfq_item = RFQItem(
            rfq_id=rfq.id,
            product_name="Enterprise Business Laptop 14-inch (Core i7 / 16GB / 512GB)",
            description="Intel i7, 16GB RAM, 512GB SSD, 3-Yr On-site Support",
            quantity=500,
            requirements_json=specs_json,
        )
        db.add(rfq_item)
        db.commit()
        db.refresh(rfq)
        print(f"Created Demo RFQ: {rfq.rfq_number} (Quantity: {rfq.quantity})")

        # 4. Seed Vendor Quotations
        # Vendor A: ₹52,000/unit | 10 days | 3 yr warranty | Net 30 | High reliability
        q_a_subtotal = 500 * 52000.0
        q_a_tax = round(q_a_subtotal * 0.18, 2)
        q_a_total = q_a_subtotal + q_a_tax

        quotation_a = Quotation(
            rfq_id=rfq.id,
            vendor_id=vendor_a.id,
            quotation_number="QUOT-TC-2026-081",
            file_name="TechCorp_Quote_500Laptops.pdf",
            delivery_days=10,
            warranty_years=3,
            payment_terms="Net 30 Days",
            tax_amount=q_a_tax,
            additional_charges=0.0,
            grand_total=q_a_total,
            extraction_confidence=0.98,
            status="EXTRACTED",
        )
        db.add(quotation_a)
        db.flush()

        db.add(QuotationItem(
            quotation_id=quotation_a.id,
            product_name="Dell Latitude 5440 Enterprise Laptop (i7-1355U / 16GB / 512GB)",
            description="Dell Latitude 5440 with 3-year ProSupport Next Business Day Onsite",
            quantity=500,
            unit_price=52000.0,
            total_price=q_a_subtotal,
        ))

        # Vendor B: ₹48,500/unit | 25 days (VIOLATION) | 5 yr warranty | Net 15 | Deliberate Total Mismatch!
        q_b_subtotal = 500 * 48500.0  # 24,250,000
        q_b_tax = round(q_b_subtotal * 0.18, 2)  # 4,365,000
        # Deliberate grand_total mismatch: 27,500,000 instead of 28,615,000
        q_b_deliberate_total = 27500000.0

        quotation_b = Quotation(
            rfq_id=rfq.id,
            vendor_id=vendor_b.id,
            quotation_number="QUOT-BH-99120",
            file_name="BudgetHardware_Laptops_Special.pdf",
            delivery_days=25,  # Delivery Violation: > 15 days
            warranty_years=5,
            payment_terms="Net 15 Days",
            tax_amount=q_b_tax,
            additional_charges=150000.0,  # Unexpected additional charges
            grand_total=q_b_deliberate_total,  # Anomaly!
            extraction_confidence=0.92,
            status="EXTRACTED",
        )
        db.add(quotation_b)
        db.flush()

        db.add(QuotationItem(
            quotation_id=quotation_b.id,
            product_name="Lenovo ThinkPad L14 Gen 4 (i7-1365U / 16GB / 512GB)",
            description="Lenovo ThinkPad L14 Gen 4 with 5-year Extended Carry-in Warranty",
            quantity=500,
            unit_price=48500.0,
            total_price=q_b_subtotal,
        ))

        # Vendor C: ₹49,800/unit | 12 days | 3 yr warranty | Net 45 | Best overall trade-off
        q_c_subtotal = 500 * 49800.0  # 24,900,000
        q_c_tax = round(q_c_subtotal * 0.18, 2)  # 4,482,000
        q_c_total = q_c_subtotal + q_c_tax

        quotation_c = Quotation(
            rfq_id=rfq.id,
            vendor_id=vendor_c.id,
            quotation_number="QUOT-PT-88341",
            file_name="PrimeTech_Commercial_Bid.pdf",
            delivery_days=12,
            warranty_years=3,
            payment_terms="Net 45 Days",
            tax_amount=q_c_tax,
            additional_charges=0.0,
            grand_total=q_c_total,
            extraction_confidence=0.99,
            status="EXTRACTED",
        )
        db.add(quotation_c)
        db.flush()

        db.add(QuotationItem(
            quotation_id=quotation_c.id,
            product_name="HP EliteBook 640 G10 (i7-1355U / 16GB / 512GB NVMe)",
            description="HP EliteBook 640 G10 with 3-year Next Business Day Onsite Carepack",
            quantity=500,
            unit_price=49800.0,
            total_price=q_c_subtotal,
        ))

        db.commit()
        print("Created 3 Quotations with Master Spec test cases.")

        # 5. Run initial Analysis
        print("Running automated quotation analysis...")
        AnalysisService.run_rfq_analysis(db=db, rfq_id=rfq.id)
        print("Analysis completed and decision trace generated.")

        print("\n=== DEMO DATA SEEDED SUCCESSFULLY ===")
        print(f"RFQ ID: {rfq.id} ({rfq.rfq_number})")
        print(f"Vendor A ID: {vendor_a.id} ({vendor_a.name})")
        print(f"Vendor B ID: {vendor_b.id} ({vendor_b.name})")
        print(f"Vendor C ID: {vendor_c.id} ({vendor_c.name})")
        print("======================================\n")

    except Exception as e:
        db.rollback()
        print(f"Error seeding demo data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
