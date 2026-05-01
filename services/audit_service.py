from datetime import datetime

from sqlalchemy.orm import Session

from database.models import AuditLog
from logging_subsystem.logger import log_event


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        event_type: str,
        component: str,
        username: str | None = None,
        user_id: int | None = None,
        ip_address: str | None = None,
        details: str | None = None,
        headers: str | None = None,
    ) -> AuditLog:
        event = log_event(event_type, component, username, user_id,
                          ip_address, details, headers)
        entry = AuditLog(
            event_id=event["event_id"],
            timestamp=datetime.utcnow(),
            event_type=event_type,
            component=component,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            details=details,
            headers=headers,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_events(self, limit: int = 200, offset: int = 0) -> list[AuditLog]:
        return (
            self.db.query(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
