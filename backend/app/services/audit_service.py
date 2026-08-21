import json
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from backend.app.models.audit_log import AuditLog


class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        entity_name: str,
        entity_id: Optional[int],
        action: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ) -> AuditLog:
        details_str = json.dumps(details, default=str) if details is not None else None
        log = AuditLog(
            entity_name=entity_name,
            entity_id=entity_id,
            action=action,
            details_json=details_str,
            user_id=user_id,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log
