from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..broker import mt5_connector
from ..database import get_db
from ..deps import get_current_user
from ..models import AuditLog, BrokerConnection, BrokerType, RiskSettings, Trade, TradeSide, TradeStatus, User
from ..risk import risk_manager
from ..schemas import LotCalculatorRequest, LotCalculatorResponse, ModifyOrderRequest, PlaceOrderRequest, TradeOut

router = APIRouter(prefix="/api/trading", tags=["trading"])


def _get_risk(db: Session, user_id: str) -> RiskSettings:
    risk = db.query(RiskSettings).filter(RiskSettings.user_id == user_id).first()
    if not risk:
        risk = RiskSettings(user_id=user_id)
        db.add(risk)
        db.commit()
        db.refresh(risk)
    return risk


@router.post("/lot-calculator", response_model=LotCalculatorResponse)
def lot_calculator(payload: LotCalculatorRequest):
    try:
        result = risk_manager.calculate_lot_size(
            payload.account_balance, payload.risk_percent, payload.stop_loss_pips, payload.pip_value_per_lot
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/order", response_model=TradeOut)
def place_order(
    payload: PlaceOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conn = db.query(BrokerConnection).filter(
        BrokerConnection.id == payload.broker_connection_id, BrokerConnection.user_id == current_user.id
    ).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Broker connection not found.")
    if conn.status != "connected":
        raise HTTPException(status_code=400, detail=f"Broker connection is not active (status={conn.status}).")

    if payload.side not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="side must be 'buy' or 'sell'.")

    risk = _get_risk(db, current_user.id)

    # Pull live account balance for risk checks
    if conn.broker_type == BrokerType.mt5:
        snapshot = mt5_connector.get_account_snapshot()
        if snapshot is None:
            raise HTTPException(status_code=400, detail="Could not fetch live account balance from broker.")
        account_balance = snapshot["balance"]
    else:
        raise HTTPException(status_code=400, detail=f"Trading not implemented for broker type {conn.broker_type}.")

    gate = risk_manager.check_can_open_trade(db, current_user.id, account_balance, risk)
    if not gate["allowed"]:
        raise HTTPException(status_code=403, detail=gate["reason"])

    # Determine lot size
    lot_size = payload.lot_size
    if lot_size is None:
        if not payload.stop_loss:
            raise HTTPException(status_code=400, detail="Provide lot_size, or stop_loss + risk_percent to auto-calculate.")
        risk_percent = payload.risk_percent or risk.risk_percent_per_trade
        # Approximate pip distance from price difference (caller should pass realistic SL)
        sl_distance_pips = risk.default_stop_loss_pips
        calc = risk_manager.calculate_lot_size(account_balance, risk_percent, sl_distance_pips)
        lot_size = calc["lot_size"]

    if conn.broker_type == BrokerType.mt5:
        result = mt5_connector.place_order(payload.symbol, payload.side, lot_size, payload.stop_loss, payload.take_profit)
    else:
        raise HTTPException(status_code=400, detail="Unsupported broker type.")

    if not result["success"]:
        db.add(AuditLog(user_id=current_user.id, action="order_rejected", detail=result["error"], level="error"))
        db.commit()
        raise HTTPException(status_code=400, detail=result["error"])

    trade = Trade(
        user_id=current_user.id,
        broker_connection_id=conn.id,
        broker_ticket=str(result.get("ticket", "")),
        symbol=payload.symbol.upper(),
        side=TradeSide.buy if payload.side == "buy" else TradeSide.sell,
        lot_size=lot_size,
        entry_price=result.get("price", 0.0),
        stop_loss=payload.stop_loss,
        take_profit=payload.take_profit,
        status=TradeStatus.open,
        is_auto=payload.is_auto,
    )
    db.add(trade)
    db.add(AuditLog(user_id=current_user.id, action="order_placed", detail=f"{payload.side} {lot_size} {payload.symbol}"))
    db.commit()
    db.refresh(trade)
    return trade


@router.post("/order/{trade_id}/close", response_model=TradeOut)
def close_order(trade_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == current_user.id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found.")
    if trade.status != TradeStatus.open:
        raise HTTPException(status_code=400, detail="Trade is not open.")

    conn = db.query(BrokerConnection).filter(BrokerConnection.id == trade.broker_connection_id).first()
    if conn and conn.broker_type == BrokerType.mt5:
        result = mt5_connector.close_order(int(trade.broker_ticket), trade.symbol, trade.side.value, trade.lot_size)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        trade.exit_price = result["price"]
        trade.profit = (trade.exit_price - trade.entry_price) * trade.lot_size * (1 if trade.side == TradeSide.buy else -1)
    else:
        raise HTTPException(status_code=400, detail="Unsupported broker type for closing.")

    trade.status = TradeStatus.closed
    trade.closed_at = datetime.utcnow()
    db.add(AuditLog(user_id=current_user.id, action="order_closed", detail=f"{trade.symbol} profit={trade.profit:.2f}"))
    db.commit()
    db.refresh(trade)
    return trade


@router.put("/order/{trade_id}/modify", response_model=TradeOut)
def modify_order(
    trade_id: str,
    payload: ModifyOrderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == current_user.id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found.")
    if trade.status != TradeStatus.open:
        raise HTTPException(status_code=400, detail="Trade is not open.")

    conn = db.query(BrokerConnection).filter(BrokerConnection.id == trade.broker_connection_id).first()
    if conn and conn.broker_type == BrokerType.mt5:
        result = mt5_connector.modify_order(int(trade.broker_ticket), payload.stop_loss, payload.take_profit)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
    else:
        raise HTTPException(status_code=400, detail="Unsupported broker type for modifying.")

    if payload.stop_loss is not None:
        trade.stop_loss = payload.stop_loss
    if payload.take_profit is not None:
        trade.take_profit = payload.take_profit
    db.commit()
    db.refresh(trade)
    return trade


@router.get("/trades", response_model=list[TradeOut])
def list_trades(status_filter: str = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Trade).filter(Trade.user_id == current_user.id)
    if status_filter:
        q = q.filter(Trade.status == status_filter)
    return q.order_by(Trade.opened_at.desc()).all()
