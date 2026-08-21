from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base


class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False)
    quotation_number = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=True)
    delivery_days = Column(Integer, nullable=False)
    warranty_years = Column(Integer, default=1, nullable=False)
    payment_terms = Column(String(255), nullable=False)
    tax_amount = Column(Float, default=0.0, nullable=False)
    additional_charges = Column(Float, default=0.0, nullable=False)
    grand_total = Column(Float, nullable=False)
    extraction_confidence = Column(Float, default=1.0, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False)  # PENDING, EXTRACTED, VALIDATED, REJECTED
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    rfq = relationship("RFQ", back_populates="quotations")
    vendor = relationship("Vendor", back_populates="quotations")
    items = relationship("QuotationItem", back_populates="quotation", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="quotation", cascade="all, delete-orphan")


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    # Relationships
    quotation = relationship("Quotation", back_populates="items")
