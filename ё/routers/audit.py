from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from auth.dependencies import require_admin
from database.engine import get_db
from database.models import User, AuditLog
from services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/")
def list_audit(
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    events = AuditService(db).list_events(limit=limit, offset=offset)
    return [
        {
            "id": e.id,
            "event_id": e.event_id,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "event_type": e.event_type,
            "component": e.component,
            "username": e.username,
            "ip_address": e.ip_address,
            "details": e.details,
            "headers": e.headers,
        }
        for e in events
    ]
