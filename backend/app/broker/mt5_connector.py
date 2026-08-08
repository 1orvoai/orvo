"""
Real MetaTrader5 integration using the official `MetaTrader5` Python package.

HONEST LIMITATION (documented, not hidden):
The MetaTrader5 package only works on Windows, and only when a MetaTrader 5
terminal is installed on the same machine and logged into a broker account.
There is no cross-platform or cloud-hosted way to use it — that is a
limitation of MetaTrader5 itself, not something ORVO fakes around.

If you're on macOS/Linux or want a cloud-deployable broker connection,
use the OANDA REST integration instead (see broker/oanda_client.py you can
add following the same interface) — OANDA has a real public HTTPS API that
works from any OS/server.

This module degrades gracefully: if the `MetaTrader5` package or a Windows
terminal isn't available, connect() returns a clear real error — never a
fake "connected" status.
"""
from typing import Optional, Dict
import platform

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


def is_supported() -> Dict:
    if platform.system() != "Windows":
        return {"supported": False, "reason": "MetaTrader5 Python package only runs on Windows."}
    if not MT5_AVAILABLE:
        return {"supported": False, "reason": "MetaTrader5 package not installed. Run: pip install MetaTrader5"}
    return {"supported": True, "reason": ""}


def connect(login: str, password: str, server: str, terminal_path: Optional[str] = None) -> Dict:
    support = is_supported()
    if not support["supported"]:
        return {"success": False, "error": support["reason"]}

    try:
        init_kwargs = {}
        if terminal_path:
            init_kwargs["path"] = terminal_path

        if not mt5.initialize(**init_kwargs):
            return {"success": False, "error": f"MT5 initialize() failed: {mt5.last_error()}"}

        authorized = mt5.login(int(login), password=password, server=server)
        if not authorized:
            error = mt5.last_error()
            mt5.shutdown()
            return {"success": False, "error": f"MT5 login failed: {error}"}

        account_info = mt5.account_info()
        if account_info is None:
            mt5.shutdown()
            return {"success": False, "error": "Connected but could not retrieve account info."}

        return {
            "success": True,
            "account": {
                "login": account_info.login,
                "balance": account_info.balance,
                "equity": account_info.equity,
                "margin": account_info.margin,
                "free_margin": account_info.margin_free,
                "currency": account_info.currency,
                "leverage": account_info.leverage,
                "server": account_info.server,
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_account_snapshot() -> Optional[Dict]:
    if not MT5_AVAILABLE:
        return None
    info = mt5.account_info()
    if info is None:
        return None
    return {
        "balance": info.balance,
        "equity": info.equity,
        "margin": info.margin,
        "free_margin": info.margin_free,
        "currency": info.currency,
    }


def place_order(symbol: str, side: str, lot_size: float,
                 stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Dict:
    if not MT5_AVAILABLE:
        return {"success": False, "error": "MetaTrader5 package not available on this system."}

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return {"success": False, "error": f"Symbol {symbol} not found on this broker."}
    if not symbol_info.visible:
        mt5.symbol_select(symbol, True)

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return {"success": False, "error": f"Could not get tick data for {symbol}."}

    price = tick.ask if side == "buy" else tick.bid
    order_type = mt5.ORDER_TYPE_BUY if side == "buy" else mt5.ORDER_TYPE_SELL

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(lot_size),
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": 20260807,
        "comment": "ORVO AI Trading Platform",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    if stop_loss:
        request["sl"] = float(stop_loss)
    if take_profit:
        request["tp"] = float(take_profit)

    result = mt5.order_send(request)
    if result is None:
        return {"success": False, "error": f"order_send returned None: {mt5.last_error()}"}
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return {"success": False, "error": f"Order rejected: retcode={result.retcode}, comment={result.comment}"}

    return {
        "success": True,
        "ticket": result.order,
        "price": result.price,
        "volume": result.volume,
    }


def close_order(ticket: int, symbol: str, side: str, lot_size: float) -> Dict:
    if not MT5_AVAILABLE:
        return {"success": False, "error": "MetaTrader5 package not available on this system."}

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return {"success": False, "error": f"Could not get tick data for {symbol}."}

    close_type = mt5.ORDER_TYPE_SELL if side == "buy" else mt5.ORDER_TYPE_BUY
    price = tick.bid if side == "buy" else tick.ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(lot_size),
        "type": close_type,
        "position": int(ticket),
        "price": price,
        "deviation": 20,
        "magic": 20260807,
        "comment": "ORVO close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        return {"success": False, "error": f"Close failed: {mt5.last_error() if result is None else result.comment}"}
    return {"success": True, "price": result.price}


def modify_order(ticket: int, stop_loss: Optional[float] = None, take_profit: Optional[float] = None) -> Dict:
    if not MT5_AVAILABLE:
        return {"success": False, "error": "MetaTrader5 package not available on this system."}

    position = mt5.positions_get(ticket=ticket)
    if not position:
        return {"success": False, "error": f"Position {ticket} not found."}
    pos = position[0]

    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": pos.symbol,
        "position": ticket,
        "sl": float(stop_loss) if stop_loss else pos.sl,
        "tp": float(take_profit) if take_profit else pos.tp,
    }
    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        return {"success": False, "error": f"Modify failed: {mt5.last_error() if result is None else result.comment}"}
    return {"success": True}


def shutdown():
    if MT5_AVAILABLE:
        mt5.shutdown()
