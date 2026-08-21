from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from backend.app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    entity_name = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=True)
    action = Column(String(100), nullable=False)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
