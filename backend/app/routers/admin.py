import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db, engine
from ..deps import get_current_admin
from ..models import AuditLog, BrokerConnection, Trade, TradeStatus, User
from ..schemas import AdminUserOut, SystemHealthOut

router = APIRouter(prefix="/api/admin", tags=["admin"])

_START_TIME = time.time()


@router.get("/users", response_model=list[AdminUserOut])
def list_users(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.put("/users/{user_id}/toggle-active")
def toggle_active(user_id: str, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = not user.is_active
    db.commit()
    return {"id": user.id, "is_active": user.is_active}


@router.get("/broker-connections")
def broker_connections(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    conns = db.query(BrokerConnection).all()
    return [
        {
            "id": c.id,
            "user_id": c.user_id,
            "broker_type": c.broker_type.value,
            "status": c.status,
            "last_error": c.last_error,
            "last_checked": c.last_checked,
        }
        for c in conns
    ]


@router.get("/logs")
def logs(limit: int = 200, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    entries = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "action": e.action,
            "detail": e.detail,
            "level": e.level,
            "created_at": e.created_at,
        }
        for e in entries
    ]


@router.get("/health", response_model=SystemHealthOut)
def health(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"error: {e}"

    return SystemHealthOut(
        status="healthy" if db_status == "healthy" else "degraded",
        database=db_status,
        uptime_seconds=round(time.time() - _START_TIME, 1),
        total_users=db.query(User).count(),
        active_broker_connections=db.query(BrokerConnection).filter(BrokerConnection.status == "connected").count(),
        open_trades=db.query(Trade).filter(Trade.status == TradeStatus.open).count(),
    )
