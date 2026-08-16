from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..broker import mt5_connector
from ..database import get_db
from ..deps import get_current_user
from ..models import AuditLog, BrokerConnection, BrokerType, User
from ..schemas import BrokerConnectionOut, MT5ConnectRequest
from ..security import encrypt_text, decrypt_text
import json

router = APIRouter(prefix="/api/broker", tags=["broker"])


@router.get("/mt5/status")
def mt5_status():
    """Tells the user honestly whether MT5 integration can run on this machine."""
    return mt5_connector.is_supported()


@router.post("/mt5/connect", response_model=BrokerConnectionOut)
def mt5_connect(
    payload: MT5ConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = mt5_connector.connect()

    creds_json = json.dumps({
        "login": payload.login,
        "password": payload.password,
        "server": payload.server,
        "terminal_path": payload.terminal_path,
    })

    conn = BrokerConnection(
        user_id=current_user.id,
        broker_type=BrokerType.mt5,
        label=payload.label or "MT5 Account",
        encrypted_credentials=encrypt_text(creds_json),
        account_login=payload.login,
        server=payload.server,
        status="connected" if result["success"] else "error",
        last_error=None if result["success"] else result["error"],
        last_checked=datetime.utcnow(),
    )
    db.add(conn)
    db.add(AuditLog(
        user_id=current_user.id,
        action="broker_connect_mt5",
        detail=f"success={result['success']}",
        level="info" if result["success"] else "error",
    ))
    db.commit()
    db.refresh(conn)

    if not result["success"]:
        # Still return 200 with the connection record (status=error) so the UI can show
        # the real reason instead of a generic failure — but also raise so callers relying
        # on a plain POST know it didn't succeed.
        raise HTTPException(status_code=400, detail=result["error"])

    return conn


@router.get("/connections", response_model=list[BrokerConnectionOut])
def list_connections(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(BrokerConnection).filter(BrokerConnection.user_id == current_user.id).all()


@router.delete("/connections/{connection_id}")
def delete_connection(connection_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conn = db.query(BrokerConnection).filter(
        BrokerConnection.id == connection_id, BrokerConnection.user_id == current_user.id
    ).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")
    db.delete(conn)
    db.commit()
    return {"message": "Broker connection removed."}


@router.get("/connections/{connection_id}/account")
def get_account_snapshot(connection_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Live balance/equity/margin pulled directly from the broker terminal."""
    conn = db.query(BrokerConnection).filter(
        BrokerConnection.id == connection_id, BrokerConnection.user_id == current_user.id
    ).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")

    if conn.broker_type == BrokerType.mt5:
        snapshot = mt5_connector.get_account_snapshot()
        if snapshot is None:
            raise HTTPException(status_code=400, detail="Could not fetch live account data. Is MT5 terminal still connected?")
        return snapshot

    raise HTTPException(status_code=400, detail=f"Live snapshot not implemented for broker type {conn.broker_type}.")
