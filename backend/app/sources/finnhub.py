import logging
import os
import threading
import time
from collections import deque
from datetime import datetime
from functools import wraps
from typing import Any

import finnhub
from sqlalchemy.orm import Session

from app.models import Stock

logger = logging.getLogger(__name__)

MAX_CALLS_PER_MINUTE = 55
MIN_MARKET_CAP = 2_000_000_000
MIN_AVG_DOLLAR_VOLUME = 50_000_000
ALLOWED_MICS = {"XNAS", "XNYS"}

_call_times: deque[float] = deque()
_lock = threading.Lock()


def _rate_limited(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with _lock:
            now = time.monotonic()
            while _call_times and now - _call_times[0] >= 60:
                _call_times.popleft()
            if len(_call_times) >= MAX_CALLS_PER_MINUTE:
                sleep_for = 60 - (now - _call_times[0]) + 0.05
                time.sleep(max(sleep_for, 0))
                now = time.monotonic()
                while _call_times and now - _call_times[0] >= 60:
                    _call_times.popleft()
            _call_times.append(time.monotonic())
        return func(*args, **kwargs)

    return wrapper


def _client() -> finnhub.Client:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        raise RuntimeError("FINNHUB_API_KEY is not set")
    return finnhub.Client(api_key=api_key)


@_rate_limited
def _stock_symbols(client: finnhub.Client) -> list[dict[str, Any]]:
    return client.stock_symbols("US")


@_rate_limited
def _company_profile(client: finnhub.Client, ticker: str) -> dict[str, Any]:
    return client.company_profile2(symbol=ticker)


@_rate_limited
def _basic_financials(client: finnhub.Client, ticker: str) -> dict[str, Any]:
    return client.company_basic_financials(ticker, "all")


@_rate_limited
def _quote(client: finnhub.Client, ticker: str) -> dict[str, Any]:
    return client.quote(ticker)


def refresh_universe(session: Session) -> int:
    client = _client()
    started = time.monotonic()
    raw = _stock_symbols(client)
    candidates = [
        s for s in raw
        if s.get("mic") in ALLOWED_MICS
        and s.get("type") == "Common Stock"
        and s.get("symbol")
        and "." not in s["symbol"]
    ]
    logger.info("Universe pre-filter: %d → %d candidates", len(raw), len(candidates))

    survivors: list[dict[str, Any]] = []
    for i, sym in enumerate(candidates, 1):
        ticker = sym["symbol"]
        try:
            profile = _company_profile(client, ticker)
        except Exception as exc:
            logger.warning("profile failed for %s: %s", ticker, exc)
            continue
        market_cap_millions = profile.get("marketCapitalization") or 0
        market_cap = market_cap_millions * 1_000_000
        if market_cap < MIN_MARKET_CAP:
            continue
        if (profile.get("country") or "").upper() != "US":
            continue
        survivors.append({"symbol": ticker, "profile": profile, "market_cap": market_cap})
        if i % 500 == 0:
            logger.info("Profile pass: %d/%d processed, %d survivors", i, len(candidates), len(survivors))

    logger.info("After market-cap filter: %d survivors", len(survivors))

    kept: list[dict[str, Any]] = []
    for i, s in enumerate(survivors, 1):
        ticker = s["symbol"]
        try:
            fin = _basic_financials(client, ticker)
            quote = _quote(client, ticker)
        except Exception as exc:
            logger.warning("financials/quote failed for %s: %s", ticker, exc)
            continue
        metric = fin.get("metric") or {}
        avg_vol_millions = metric.get("10DayAverageTradingVolume")
        price = quote.get("c")
        if not avg_vol_millions or not price:
            continue
        avg_dollar_volume = avg_vol_millions * 1_000_000 * price
        if avg_dollar_volume < MIN_AVG_DOLLAR_VOLUME:
            continue
        s["avg_volume"] = avg_vol_millions * 1_000_000
        s["price"] = price
        kept.append(s)
        if i % 200 == 0:
            logger.info("ADV pass: %d/%d processed, %d kept", i, len(survivors), len(kept))

    for s in kept:
        ticker = s["symbol"]
        profile = s["profile"]
        existing = session.query(Stock).filter_by(ticker=ticker).one_or_none()
        if existing:
            existing.name = profile.get("name")
            existing.sector = profile.get("finnhubIndustry")
            existing.market_cap = s["market_cap"]
            existing.avg_volume = s["avg_volume"]
            existing.updated_at = datetime.utcnow()
        else:
            session.add(Stock(
                ticker=ticker,
                name=profile.get("name"),
                sector=profile.get("finnhubIndustry"),
                market_cap=s["market_cap"],
                avg_volume=s["avg_volume"],
            ))
    session.commit()

    elapsed = time.monotonic() - started
    logger.info("Universe refresh complete: %d stocks in %.0fs", len(kept), elapsed)
    return len(kept)


def fetch_quote(ticker: str) -> dict[str, Any]:
    client = _client()
    q = _quote(client, ticker)
    ts = q.get("t")
    return {
        "price": q.get("c"),
        "volume": None,
        "timestamp": datetime.fromtimestamp(ts) if ts else None,
    }
