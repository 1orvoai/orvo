from fastapi import APIRouter, Depends, HTTPException, Query

from ..ai import signal_engine, technical_analysis as ta
from ..broker import binance_client
from ..deps import get_current_user
from ..models import User

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/analyze")
async def analyze(
    symbol: str = Query(...),
    timeframe: str = Query("1h"),
    current_user: User = Depends(get_current_user),
):
    try:
        candles = await binance_client.get_klines(symbol, timeframe, 200)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch market data for analysis: {e}")

    if len(candles) < 55:
        raise HTTPException(status_code=400, detail="Not enough candle history returned to run analysis.")

    df = ta.candles_to_df(candles)
    result = signal_engine.analyze(df, symbol.upper(), timeframe)
    return result
