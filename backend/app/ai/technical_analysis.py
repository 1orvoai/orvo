"""
Deterministic technical-analysis engine built on real OHLCV data.
Every function here is a real, explainable calculation (no randomness, no fake data).
This is classic technical analysis math — it is a decision-support tool, not a
guarantee of profit. No one can honestly promise that.
"""
from datetime import datetime, timezone
from typing import List, Dict
import pandas as pd
import numpy as np


def candles_to_df(candles: List[Dict]) -> pd.DataFrame:
    df = pd.DataFrame(candles)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def detect_trend(df: pd.DataFrame) -> str:
    """EMA20 vs EMA50 crossover + recent higher-highs/higher-lows structure."""
    if len(df) < 55:
        return "insufficient_data"
    ema20 = ema(df["close"], 20)
    ema50 = ema(df["close"], 50)
    last20, last50 = ema20.iloc[-1], ema50.iloc[-1]

    recent = df.tail(20)
    highs_rising = recent["high"].iloc[-5:].mean() > recent["high"].iloc[-15:-5].mean()
    lows_rising = recent["low"].iloc[-5:].mean() > recent["low"].iloc[-15:-5].mean()

    if last20 > last50 and highs_rising and lows_rising:
        return "uptrend"
    if last20 < last50 and not highs_rising and not lows_rising:
        return "downtrend"
    return "ranging"


def detect_support_resistance(df: pd.DataFrame, lookback: int = 60, tolerance_pct: float = 0.15) -> Dict:
    """Pivot-based support/resistance: local swing highs/lows clustered within tolerance."""
    recent = df.tail(lookback).reset_index(drop=True)
    swing_highs, swing_lows = [], []
    for i in range(2, len(recent) - 2):
        window = recent.iloc[i - 2:i + 3]
        if recent["high"][i] == window["high"].max():
            swing_highs.append(recent["high"][i])
        if recent["low"][i] == window["low"].min():
            swing_lows.append(recent["low"][i])

    def cluster(levels: List[float]) -> List[float]:
        if not levels:
            return []
        levels = sorted(levels)
        clusters = [[levels[0]]]
        for lvl in levels[1:]:
            if abs(lvl - clusters[-1][-1]) / clusters[-1][-1] * 100 <= tolerance_pct:
                clusters[-1].append(lvl)
            else:
                clusters.append([lvl])
        return [round(sum(c) / len(c), 6) for c in clusters]

    return {
        "resistance": [float(x) for x in cluster(swing_highs)[-5:]],
        "support": [float(x) for x in cluster(swing_lows)[-5:]],
    }


def detect_market_structure(df: pd.DataFrame) -> str:
    trend = detect_trend(df)
    if trend == "uptrend":
        return "higher_highs_higher_lows"
    if trend == "downtrend":
        return "lower_highs_lower_lows"
    return "consolidation"


def detect_bos_choch(df: pd.DataFrame, lookback: int = 30) -> str:
    """
    Break of Structure / Change of Character detection.
    BOS: price closes beyond the most recent significant swing high/low in the direction
         of the existing trend (trend continuation).
    CHOCH: price closes beyond the most recent swing point AGAINST the prevailing trend
           (early reversal signal).
    """
    recent = df.tail(lookback).reset_index(drop=True)
    if len(recent) < 10:
        return "insufficient_data"

    swing_high_idx = recent["high"].iloc[:-3].idxmax()
    swing_low_idx = recent["low"].iloc[:-3].idxmin()
    swing_high = recent["high"].iloc[swing_high_idx]
    swing_low = recent["low"].iloc[swing_low_idx]
    last_close = recent["close"].iloc[-1]
    trend = detect_trend(df)

    if last_close > swing_high:
        return "bos_bullish" if trend == "uptrend" else "choch_bullish"
    if last_close < swing_low:
        return "bos_bearish" if trend == "downtrend" else "choch_bearish"
    return "no_break"


def detect_fair_value_gaps(df: pd.DataFrame, lookback: int = 40) -> List[Dict]:
    """
    3-candle FVG: gap between candle[i-1].high and candle[i+1].low (bullish),
    or candle[i-1].low and candle[i+1].high (bearish), left unfilled by candle[i].
    """
    recent = df.tail(lookback).reset_index(drop=True)
    gaps = []
    for i in range(1, len(recent) - 1):
        prev_c, next_c = recent.iloc[i - 1], recent.iloc[i + 1]
        if next_c["low"] > prev_c["high"]:
            gaps.append({
                "type": "bullish",
                "top": round(float(next_c["low"]), 6),
                "bottom": round(float(prev_c["high"]), 6),
                "index": i,
            })
        elif next_c["high"] < prev_c["low"]:
            gaps.append({
                "type": "bearish",
                "top": round(float(prev_c["low"]), 6),
                "bottom": round(float(next_c["high"]), 6),
                "index": i,
            })
    return gaps[-5:]


def detect_order_blocks(df: pd.DataFrame, lookback: int = 50) -> List[Dict]:
    """
    Simplified order block detection: the last opposite-colored candle before a strong
    directional impulse (move whose range exceeds 1.5x the local ATR).
    """
    recent = df.tail(lookback).reset_index(drop=True)
    period_atr = atr(recent, 14)
    blocks = []
    for i in range(15, len(recent) - 1):
        candle = recent.iloc[i]
        candle_range = candle["high"] - candle["low"]
        local_atr = period_atr.iloc[i]
        if pd.isna(local_atr) or local_atr == 0:
            continue
        is_impulsive = candle_range > 1.5 * local_atr
        if not is_impulsive:
            continue
        bullish_impulse = candle["close"] > candle["open"]
        prev = recent.iloc[i - 1]
        prev_bearish = prev["close"] < prev["open"]
        prev_bullish = prev["close"] > prev["open"]
        if bullish_impulse and prev_bearish:
            blocks.append({
                "type": "bullish_ob",
                "top": round(float(prev["high"]), 6),
                "bottom": round(float(prev["low"]), 6),
                "index": i - 1,
            })
        elif not bullish_impulse and prev_bullish:
            blocks.append({
                "type": "bearish_ob",
                "top": round(float(prev["high"]), 6),
                "bottom": round(float(prev["low"]), 6),
                "index": i - 1,
            })
    return blocks[-5:]


def detect_supply_demand_zones(df: pd.DataFrame, lookback: int = 60) -> Dict:
    """Zones built from clusters of rejection wicks around support/resistance."""
    sr = detect_support_resistance(df, lookback)
    recent = df.tail(lookback)
    atr_val = float(atr(recent, 14).iloc[-1]) if len(recent) >= 14 else 0.0
    supply = [{"top": round(r + atr_val * 0.5, 6), "bottom": round(r, 6)} for r in sr["resistance"]]
    demand = [{"top": round(s, 6), "bottom": round(s - atr_val * 0.5, 6)} for s in sr["support"]]
    return {"supply": supply, "demand": demand}


def detect_volatility(df: pd.DataFrame) -> float:
    period_atr = atr(df, 14)
    return round(float(period_atr.iloc[-1]), 6) if not period_atr.empty else 0.0


def detect_volume_signal(df: pd.DataFrame) -> str:
    if len(df) < 20:
        return "insufficient_data"
    avg_vol = df["volume"].tail(20).mean()
    last_vol = df["volume"].iloc[-1]
    if last_vol > avg_vol * 1.5:
        return "spike_above_average"
    if last_vol < avg_vol * 0.5:
        return "below_average"
    return "average"


def detect_session(now: datetime = None) -> str:
    """Detects the active forex trading session based on UTC time."""
    now = now or datetime.now(timezone.utc)
    hour = now.hour
    sessions = []
    if 0 <= hour < 9:
        sessions.append("Asian")
    if 7 <= hour < 16:
        sessions.append("London")
    if 12 <= hour < 21:
        sessions.append("New York")
    return " + ".join(sessions) if sessions else "Off-hours"


def detect_breakout(df: pd.DataFrame, lookback: int = 20) -> str:
    if len(df) < lookback + 1:
        return "insufficient_data"
    recent = df.tail(lookback + 1)
    range_high = recent["high"].iloc[:-1].max()
    range_low = recent["low"].iloc[:-1].min()
    last_close = recent["close"].iloc[-1]
    if last_close > range_high:
        return "bullish_breakout"
    if last_close < range_low:
        return "bearish_breakout"
    return "no_breakout"
