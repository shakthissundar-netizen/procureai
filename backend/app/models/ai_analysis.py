from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.app.database import Base


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rfq_id = Column(Integer, ForeignKey("rfqs.id", ondelete="CASCADE"), nullable=False)
    recommended_vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    summary = Column(Text, nullable=False)
    decision_trace_json = Column(Text, nullable=False)  # JSON formatted decision explanation
    negotiation_strategy = Column(Text, nullable=True)  # Negotiation tactics per vendor
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    rfq = relationship("RFQ", back_populates="analyses")
    recommended_vendor = relationship("Vendor")
