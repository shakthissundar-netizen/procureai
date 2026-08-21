from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    company = Column(String(255), nullable=False)
    category = Column(String(100), default="General", nullable=False)
    rating = Column(Float, default=4.0, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    quotations = relationship("Quotation", back_populates="vendor", cascade="all, delete-orphan")
    scores = relationship("VendorScore", back_populates="vendor", cascade="all, delete-orphan")
    anomalies = relationship("Anomaly", back_populates="vendor", cascade="all, delete-orphan")
    purchase_orders = relationship("PurchaseOrder", back_populates="vendor", cascade="all, delete-orphan")
