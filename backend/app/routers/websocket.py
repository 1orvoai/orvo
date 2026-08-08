import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..broker import binance_client
from ..config import settings

router = APIRouter()


@router.websocket("/ws/market/{symbol}")
async def market_ws(websocket: WebSocket, symbol: str):
    """
    Streams live price updates for a symbol to the browser by polling Binance's
    public REST ticker endpoint every 2 seconds and pushing it over our own
    WebSocket. (A direct proxy to Binance's WS stream can be swapped in later —
    polling keeps this dependency-free and reliable for a local dev server.)
    """
    await websocket.accept()
    try:
        while True:
            try:
                ticker = await binance_client.get_ticker(symbol)
                await websocket.send_text(json.dumps({"type": "ticker", "data": ticker}))
            except Exception as e:
                await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass


@router.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket):
    """Pushes a heartbeat + live multi-symbol tickers for the dashboard watchlist widget."""
    await websocket.accept()
    try:
        while True:
            try:
                tickers = await binance_client.get_multiple_tickers(settings.DEFAULT_SYMBOLS)
                await websocket.send_text(json.dumps({"type": "watchlist", "data": tickers}))
            except Exception as e:
                await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        pass
