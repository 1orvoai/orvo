"""
Real risk-management calculations used before/while placing and managing trades.
No part of this module is decorative — every function is actually invoked by the
trading router before an order reaches a broker connector.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from ..models import Trade, TradeStatus, RiskSettings


def calculate_lot_size(account_balance: float, risk_percent: float,
                        stop_loss_pips: float, pip_value_per_lot: float = 10.0) -> dict:
    """
    Standard forex position sizing formula:
    lot_size = (account_balance * risk_percent / 100) / (stop_loss_pips * pip_value_per_lot)
    """
    if stop_loss_pips <= 0:
        raise ValueError("stop_loss_pips must be greater than 0")
    risk_amount = account_balance * (risk_percent / 100)
    lot_size = risk_amount / (stop_loss_pips * pip_value_per_lot)
    return {
        "lot_size": round(max(lot_size, 0.01), 2),
        "risk_amount": round(risk_amount, 2),
        "formula": "lot_size = (balance * risk% / 100) / (stop_loss_pips * pip_value_per_lot)",
    }


def get_daily_trades(db: Session, user_id: str) -> List[Trade]:
    today = datetime.now(timezone.utc).date()
    return [
        t for t in db.query(Trade).filter(Trade.user_id == user_id).all()
        if t.opened_at.date() == today
    ]


def get_daily_pl(db: Session, user_id: str) -> float:
    trades = get_daily_trades(db, user_id)
    return round(sum(t.profit for t in trades), 2)


def check_can_open_trade(db: Session, user_id: str, account_balance: float,
                          risk: RiskSettings) -> dict:
    """
    Returns {"allowed": bool, "reason": str}. Called before every new order.
    Enforces: daily loss limit, daily profit target, max drawdown, max open trades.
    """
    daily_pl = get_daily_pl(db, user_id)
    daily_loss_limit = -abs(account_balance * (risk.daily_loss_limit_percent / 100))
    daily_profit_target = account_balance * (risk.daily_profit_target_percent / 100)

    if daily_pl <= daily_loss_limit:
        return {"allowed": False, "reason": f"Daily loss limit reached ({daily_pl:.2f} <= {daily_loss_limit:.2f}). Trading halted for today."}

    if daily_pl >= daily_profit_target:
        return {"allowed": False, "reason": f"Daily profit target reached ({daily_pl:.2f} >= {daily_profit_target:.2f}). Trading halted for today."}

    open_trades = db.query(Trade).filter(Trade.user_id == user_id, Trade.status == TradeStatus.open).count()
    if open_trades >= risk.max_open_trades:
        return {"allowed": False, "reason": f"Max open trades limit reached ({open_trades}/{risk.max_open_trades})."}

    closed_trades = db.query(Trade).filter(Trade.user_id == user_id, Trade.status == TradeStatus.closed).all()
    if closed_trades:
        peak = account_balance
        running = account_balance
        max_dd = 0.0
        for t in sorted(closed_trades, key=lambda x: x.closed_at or x.opened_at):
            running += t.profit
            peak = max(peak, running)
            dd = (peak - running) / peak * 100 if peak else 0
            max_dd = max(max_dd, dd)
        if max_dd >= risk.max_drawdown_percent:
            return {"allowed": False, "reason": f"Max drawdown exceeded ({max_dd:.1f}% >= {risk.max_drawdown_percent}%). Trading halted."}

    return {"allowed": True, "reason": "OK"}


def should_auto_close_daily_loss(db: Session, user_id: str, account_balance: float, risk: RiskSettings) -> bool:
    if not risk.auto_close_on_daily_loss:
        return False
    daily_pl = get_daily_pl(db, user_id)
    limit = -abs(account_balance * (risk.daily_loss_limit_percent / 100))
    return daily_pl <= limit


def apply_trailing_stop(current_price: float, entry_price: float, side: str,
                         current_sl: Optional[float], trailing_pips: float, pip_size: float = 0.0001) -> Optional[float]:
    """Moves SL to lock in profit as price moves favorably. Returns new SL or None if unchanged."""
    trail_distance = trailing_pips * pip_size
    if side == "buy":
        new_sl = current_price - trail_distance
        if current_sl is None or new_sl > current_sl:
            return round(new_sl, 6)
    else:  # sell
        new_sl = current_price + trail_distance
        if current_sl is None or new_sl < current_sl:
            return round(new_sl, 6)
    return None


def apply_breakeven(current_price: float, entry_price: float, side: str,
                     trigger_pips: float, pip_size: float = 0.0001) -> Optional[float]:
    """Moves SL to entry price once trade is in profit by trigger_pips. Returns new SL or None."""
    trigger_distance = trigger_pips * pip_size
    if side == "buy" and current_price - entry_price >= trigger_distance:
        return round(entry_price, 6)
    if side == "sell" and entry_price - current_price >= trigger_distance:
        return round(entry_price, 6)
    return None


def calculate_win_rate(db: Session, user_id: str) -> float:
    closed = db.query(Trade).filter(Trade.user_id == user_id, Trade.status == TradeStatus.closed).all()
    if not closed:
        return 0.0
    wins = sum(1 for t in closed if t.profit > 0)
    return round(wins / len(closed) * 100, 1)


def calculate_risk_score(db: Session, user_id: str, risk: RiskSettings) -> float:
    """
    0-100 composite risk score based on: proximity to daily loss limit,
    number of open trades relative to max, and current drawdown trend.
    Higher = riskier.
    """
    daily_pl = get_daily_pl(db, user_id)
    open_trades = db.query(Trade).filter(Trade.user_id == user_id, Trade.status == TradeStatus.open).count()

    loss_component = 0.0
    if daily_pl < 0 and risk.daily_loss_limit_percent > 0:
        loss_component = min(abs(daily_pl) / (risk.daily_loss_limit_percent), 1.0) * 50

    exposure_component = min(open_trades / max(risk.max_open_trades, 1), 1.0) * 50

    return round(loss_component + exposure_component, 1)
