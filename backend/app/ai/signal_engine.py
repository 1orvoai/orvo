"""
Composite signal engine. Combines every detector in technical_analysis.py into a
weighted confidence score and a human-readable explanation.

IMPORTANT / HONEST DISCLOSURE:
This produces a transparent, rule-based confidence score (0-100) from real price
action — it is NOT a prediction guarantee and no legitimate system can promise
profitable trades. Treat it as a decision-support signal, same as any technical
analysis a professional trader would perform by hand — just automated and explained.
"""
from datetime import datetime, timezone
from typing import Dict

from . import technical_analysis as ta


WEIGHTS = {
    "trend": 25,
    "structure_break": 20,
    "breakout": 15,
    "volume": 15,
    "fvg_ob_confluence": 15,
    "session": 10,
}


def analyze(df, symbol: str, timeframe: str) -> Dict:
    trend = ta.detect_trend(df)
    sr = ta.detect_support_resistance(df)
    structure = ta.detect_market_structure(df)
    bos_choch = ta.detect_bos_choch(df)
    fvgs = ta.detect_fair_value_gaps(df)
    obs = ta.detect_order_blocks(df)
    sd_zones = ta.detect_supply_demand_zones(df)
    volatility = ta.detect_volatility(df)
    volume_signal = ta.detect_volume_signal(df)
    session = ta.detect_session()
    breakout = ta.detect_breakout(df)

    last_close = float(df["close"].iloc[-1])

    score = 0.0
    reasons = []

    # Trend component
    if trend == "uptrend":
        score += WEIGHTS["trend"]
        reasons.append("Price is in a confirmed uptrend (EMA20 > EMA50 with rising highs/lows).")
    elif trend == "downtrend":
        score += WEIGHTS["trend"]
        reasons.append("Price is in a confirmed downtrend (EMA20 < EMA50 with falling highs/lows).")
    else:
        reasons.append("Market is ranging / no clear trend — lower directional conviction.")

    # Structure break component
    if "bos" in bos_choch:
        score += WEIGHTS["structure_break"]
        reasons.append(f"Break of Structure detected ({bos_choch}) confirming trend continuation.")
    elif "choch" in bos_choch:
        score += WEIGHTS["structure_break"] * 0.6
        reasons.append(f"Change of Character detected ({bos_choch}) — possible early reversal, reduces confidence.")
    else:
        reasons.append("No structural break in recent price action.")

    # Breakout component
    if breakout != "no_breakout" and breakout != "insufficient_data":
        score += WEIGHTS["breakout"]
        reasons.append(f"Price broke out of its {20}-candle range ({breakout}).")
    else:
        reasons.append("Price still contained within recent range — no breakout confirmation.")

    # Volume component
    if volume_signal == "spike_above_average":
        score += WEIGHTS["volume"]
        reasons.append("Volume spike above 20-period average supports conviction behind the move.")
    elif volume_signal == "average":
        score += WEIGHTS["volume"] * 0.5
        reasons.append("Volume is average — moderate participation.")
    else:
        reasons.append("Volume is below average — weak participation, lowers confidence.")

    # FVG / Order block confluence
    near_fvg = any(f["bottom"] <= last_close <= f["top"] for f in fvgs)
    near_ob = any(o["bottom"] <= last_close <= o["top"] for o in obs)
    if near_fvg or near_ob:
        score += WEIGHTS["fvg_ob_confluence"]
        reasons.append("Price is currently trading inside an unfilled Fair Value Gap or Order Block zone.")
    else:
        reasons.append("Price is not currently inside a key FVG/Order Block zone.")

    # Session
    if session in ("London", "New York", "London + New York"):
        score += WEIGHTS["session"]
        reasons.append(f"Active session: {session} — historically higher liquidity/volatility window.")
    else:
        reasons.append(f"Active session: {session} — typically lower liquidity.")

    confidence = round(min(score, 100), 1)

    # Direction & recommendation
    direction = "buy" if trend == "uptrend" else "sell" if trend == "downtrend" else "neutral"
    if confidence < 45 or direction == "neutral":
        recommendation = "avoid"
    else:
        recommendation = direction

    entry_price = last_close if recommendation in ("buy", "sell") else None
    stop_loss = None
    take_profit = None
    if recommendation == "buy":
        stop_loss = round(last_close - volatility * 1.5, 6)
        take_profit = round(last_close + volatility * 3, 6)
    elif recommendation == "sell":
        stop_loss = round(last_close + volatility * 1.5, 6)
        take_profit = round(last_close - volatility * 3, 6)

    explanation = " ".join(reasons)
    if recommendation == "avoid":
        explanation += " Overall confidence is below the 45% threshold required to recommend a trade — ORVO avoids low-conviction entries by design."

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "trend": trend,
        "confidence": confidence,
        "support_levels": sr["support"],
        "resistance_levels": sr["resistance"],
        "volatility_atr": volatility,
        "market_structure": structure,
        "bos_choch": bos_choch,
        "fair_value_gaps": fvgs,
        "order_blocks": obs,
        "supply_zones": sd_zones["supply"],
        "demand_zones": sd_zones["demand"],
        "session": session,
        "recommendation": recommendation,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "explanation": explanation,
        "generated_at": datetime.now(timezone.utc),
    }
