from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False)
    quotation_id = Column(Integer, ForeignKey("quotations.id", ondelete="CASCADE"), nullable=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=True)
    type = Column(String(100), nullable=False)  # DELIVERY_VIOLATION, WARRANTY_VIOLATION, PRICE_MISMATCH, TAX_INCONSISTENCY, CHARGE_ANOMALY, MISSING_FIELD, SUSPICIOUS_PRICING
    severity = Column(String(50), nullable=False, default="WARNING")  # CRITICAL, WARNING, INFO
    message = Column(Text, nullable=False)
    expected_value = Column(String(255), nullable=True)
    actual_value = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    rfq = relationship("RFQ", back_populates="anomalies")
    quotation = relationship("Quotation", back_populates="anomalies")
    vendor = relationship("Vendor", back_populates="anomalies")
