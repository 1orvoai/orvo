from fastapi import APIRouter, HTTPException, Query

from ..broker import binance_client
from ..config import settings

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/symbols")
def list_symbols():
    return {"symbols": settings.DEFAULT_SYMBOLS}


@router.get("/candles")
async def get_candles(symbol: str = Query(...), interval: str = Query("1h"), limit: int = Query(200, le=1000)):
    try:
        candles = await binance_client.get_klines(symbol, interval, limit)
        return {"symbol": symbol.upper(), "interval": interval, "candles": candles}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch market data: {e}")


@router.get("/ticker")
async def get_ticker(symbol: str = Query(...)):
    try:
        return await binance_client.get_ticker(symbol)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch ticker: {e}")


@router.get("/tickers")
async def get_tickers():
    try:
        return {"tickers": await binance_client.get_multiple_tickers(settings.DEFAULT_SYMBOLS)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch tickers: {e}")
