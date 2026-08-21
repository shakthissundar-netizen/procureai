from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base


class RFQ(Base):
    __tablename__ = "rfqs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rfq_number = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="OPEN", nullable=False)  # OPEN, ANALYZED, APPROVED, CLOSED
    target_unit_price = Column(Float, nullable=False)
    max_delivery_days = Column(Integer, nullable=False)
    min_warranty_years = Column(Integer, default=1, nullable=False)
    created_by = Column(String(255), default="Procurement Manager", nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    items = relationship("RFQItem", back_populates="rfq", cascade="all, delete-orphan")
    quotations = relationship("Quotation", back_populates="rfq", cascade="all, delete-orphan")
    scores = relationship("VendorScore", back_populates="rfq", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="rfq", cascade="all, delete-orphan")
    analyses = relationship("AIAnalysis", back_populates="rfq", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="rfq", cascade="all, delete-orphan")


class RFQItem(Base):
    __tablename__ = "rfq_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    requirements_json = Column(Text, nullable=True)  # JSON string of detailed specs

    # Relationships
    rfq = relationship("RFQ", back_populates="items")
