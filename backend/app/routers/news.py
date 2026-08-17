"""
Economic calendar / high-impact news integration.
Requires a free API key from either:
  - Finnhub (https://finnhub.io) -> set NEWS_API_PROVIDER=finnhub and NEWS_API_KEY
  - Financial Modeling Prep (https://financialmodelingprep.com) -> NEWS_API_PROVIDER=fmp

Without a key configured, this endpoint returns a clear "not configured" response
rather than fabricating calendar data — fake economic events would be actively
dangerous for a trading tool.
"""
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, HTTPException

from ..config import settings

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/economic-calendar")
async def economic_calendar():
    if not settings.NEWS_API_KEY or not settings.NEWS_API_PROVIDER:
        return {
            "configured": False,
            "message": (
                "Economic calendar is not configured. Get a free API key from finnhub.io "
                "or financialmodelingprep.com and set NEWS_API_PROVIDER + NEWS_API_KEY in your .env file."
            ),
            "events": [],
        }

    today = datetime.utcnow().date()
    end = today + timedelta(days=7)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if settings.NEWS_API_PROVIDER == "finnhub":
                resp = await client.get(
                    "https://finnhub.io/api/v1/calendar/economic",
                    params={"from": str(today), "to": str(end), "token": settings.NEWS_API_KEY},
                )
                resp.raise_for_status()
                data = resp.json()
                events = [
                    {
                        "event": e.get("event"),
                        "country": e.get("country"),
                        "impact": e.get("impact"),
                        "actual": e.get("actual"),
                        "estimate": e.get("estimate"),
                        "previous": e.get("prev"),
                        "time": e.get("time"),
                    }
                    for e in data.get("economicCalendar", [])
                ]
            elif settings.NEWS_API_PROVIDER == "fmp":
                resp = await client.get(
                    "https://financialmodelingprep.com/stable/economic-calendar",
                    params={"from": str(today), "to": str(end), "apikey": settings.NEWS_API_KEY},
                )
                resp.raise_for_status()
                data = resp.json()
                events = [
                    {
                        "event": e.get("event"),
                        "country": e.get("country"),
                        "impact": e.get("impact"),
                        "actual": e.get("actual"),
                        "estimate": e.get("estimate"),
                        "previous": e.get("previous"),
                        "time": e.get("date"),
                    }
                    for e in data
                ]
            else:
                raise HTTPException(status_code=400, detail="Unknown NEWS_API_PROVIDER.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch economic calendar: {e}")

    high_impact = [e for e in events if str(e.get("impact", "")).lower() in ("high", "3")]

    return {"configured": True, "events": events, "high_impact_events": high_impact}
