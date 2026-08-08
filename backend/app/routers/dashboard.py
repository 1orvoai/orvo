from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..broker import mt5_connector
from ..database import get_db
from ..deps import get_current_user
from ..models import BrokerConnection, BrokerType, RiskSettings, Trade, TradeStatus, User
from ..risk import risk_manager

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    risk = db.query(RiskSettings).filter(RiskSettings.user_id == current_user.id).first()
    if not risk:
        risk = RiskSettings(user_id=current_user.id)
        db.add(risk)
        db.commit()
        db.refresh(risk)

    # Live account figures from the first connected broker, if any
    account = {"balance": 0.0, "equity": 0.0, "margin": 0.0, "free_margin": 0.0, "currency": "USD"}
    conn = (
        db.query(BrokerConnection)
        .filter(BrokerConnection.user_id == current_user.id, BrokerConnection.status == "connected")
        .first()
    )
    if conn and conn.broker_type == BrokerType.mt5:
        snapshot = mt5_connector.get_account_snapshot()
        if snapshot:
            account = snapshot

    daily_pl = risk_manager.get_daily_pl(db, current_user.id)
    all_closed = db.query(Trade).filter(Trade.user_id == current_user.id, Trade.status == TradeStatus.closed).all()
    total_profit = round(sum(t.profit for t in all_closed), 2)
    win_rate = risk_manager.calculate_win_rate(db, current_user.id)
    open_trades = db.query(Trade).filter(Trade.user_id == current_user.id, Trade.status == TradeStatus.open).count()
    risk_score = risk_manager.calculate_risk_score(db, current_user.id, risk)

    daily_trades = risk_manager.get_daily_trades(db, current_user.id)

    return {
        "balance": account["balance"],
        "equity": account["equity"],
        "margin": account["margin"],
        "free_margin": account["free_margin"],
        "currency": account.get("currency", "USD"),
        "daily_pl": daily_pl,
        "total_profit": total_profit,
        "win_rate": win_rate,
        "open_trades": open_trades,
        "trades_today": len(daily_trades),
        "risk_score": risk_score,
        "auto_trading_enabled": risk.auto_trading_enabled,
        "broker_connected": conn is not None,
    }


@router.get("/equity-curve")
def equity_curve(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Cumulative P/L over closed trades, oldest to newest — feeds the dashboard chart."""
    trades = (
        db.query(Trade)
        .filter(Trade.user_id == current_user.id, Trade.status == TradeStatus.closed)
        .order_by(Trade.closed_at.asc())
        .all()
    )
    points = []
    running = 0.0
    for t in trades:
        running += t.profit
        points.append({"date": t.closed_at.isoformat() if t.closed_at else None, "cumulative_pl": round(running, 2)})
    return {"points": points}
