import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from auth.dependencies import require_admin
from database.engine import get_db
from database.models import User, AuditLog, CalculationRecord, Session as DBSession

router = APIRouter(prefix="/db", tags=["db"])


@router.get("/users")
async def db_users(admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "is_active": u.is_active,
            "must_change_password": u.must_change_password,
            "failed_attempts": u.failed_attempts,
            "locked_until": u.locked_until.isoformat() if u.locked_until else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        }
        for u in rows
    ]


@router.get("/sessions")
async def db_sessions(admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(DBSession).order_by(DBSession.issued_at.desc()).limit(100).all()
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "jti": s.jti,
            "issued_at": s.issued_at.isoformat() if s.issued_at else None,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            "revoked": s.revoked,
        }
        for s in rows
    ]


@router.get("/calculations")
async def db_calculations(admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(CalculationRecord).order_by(CalculationRecord.created_at.desc()).limit(100).all()
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "input": json.loads(r.input_json),
            "result": json.loads(r.result_json),
        }
        for r in rows
    ]


@router.get("/audit-logs")
async def db_audit(admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
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
        }
        for e in rows
    ]
