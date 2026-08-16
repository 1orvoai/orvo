import os
from typing import Dict, Optional

import requests


MT5_BRIDGE_URL = os.getenv(
    "MT5_BRIDGE_URL",
    "http://194.146.38.31:8000"
)


def _get(endpoint: str) -> Dict:
    try:
        response = requests.get(
            f"{MT5_BRIDGE_URL}{endpoint}",
            timeout=15
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"MT5 bridge connection failed: {str(e)}"
        }


def _post(endpoint: str, data: Dict) -> Dict:
    try:
        response = requests.post(
            f"{MT5_BRIDGE_URL}{endpoint}",
            json=data,
            timeout=15
        )
        response.raise_for_status()
        return response.json()

    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"MT5 bridge connection failed: {str(e)}"
        }


def is_supported() -> bool:
    return True


def connect() -> Dict:
    result = _get("/mt5/status")

    if result.get("connected") is True:
        return {
            "success": True,
            **result,
        }

    return {
        "success": False,
        **result,
    }


def status() -> Dict:
    return _get("/mt5/status")


def place_order(
    symbol: str,
    lot_size: float,
    side: str,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
) -> Dict:

    return _post(
        "/mt5/order",
        {
            "symbol": symbol,
            "volume": float(lot_size),
            "side": side,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }
    )


def close_order(
    ticket: int,
    symbol: str,
    side: str,
    lot_size: float
) -> Dict:

    return _post(
        "/mt5/close",
        {
            "ticket": int(ticket),
            "symbol": symbol,
            "side": side,
            "volume": float(lot_size),
        }
    )


def modify_order(
    ticket: int,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None
) -> Dict:

    return _post(
        "/mt5/modify",
        {
            "ticket": int(ticket),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        }
    )


def shutdown() -> Dict:
    return {"success": True}


def get_account_snapshot() -> Dict:
    result = _get("/mt5/status")

    return {
        "balance": float(result.get("balance", 0)),
        "equity": float(result.get("equity", 0)),
        "margin": float(result.get("margin", 0)),
        "free_margin": float(result.get("free_margin", 0)),
        "currency": result.get("currency", "USD"),
    }
