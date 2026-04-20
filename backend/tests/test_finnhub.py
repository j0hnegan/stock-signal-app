import time
from unittest.mock import patch

import pytest

from app.models import Stock
from app.sources import finnhub as finnhub_source


SYMBOLS_FIXTURE = [
    {"symbol": "GOOD", "mic": "XNAS", "type": "Common Stock"},
    {"symbol": "OTC1", "mic": "OOTC", "type": "Common Stock"},
    {"symbol": "WARR", "mic": "XNAS", "type": "Warrant"},
    {"symbol": "SMALL", "mic": "XNAS", "type": "Common Stock"},
    {"symbol": "ILLIQUID", "mic": "XNYS", "type": "Common Stock"},
]

PROFILES = {
    "GOOD": {"name": "Good Co", "marketCapitalization": 50_000, "country": "US", "finnhubIndustry": "Tech"},
    "SMALL": {"name": "Small Co", "marketCapitalization": 100, "country": "US", "finnhubIndustry": "Tech"},
    "ILLIQUID": {"name": "Illiq Co", "marketCapitalization": 10_000, "country": "US", "finnhubIndustry": "Tech"},
}

FINANCIALS = {
    "GOOD": {"metric": {"10DayAverageTradingVolume": 5.0}},
    "ILLIQUID": {"metric": {"10DayAverageTradingVolume": 0.1}},
}

QUOTES = {
    "GOOD": {"c": 100.0, "t": 1700000000},
    "ILLIQUID": {"c": 50.0, "t": 1700000000},
}


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    finnhub_source._call_times.clear()
    yield
    finnhub_source._call_times.clear()


def test_refresh_universe_filters_correctly(db_session, monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "fake")

    class FakeClient:
        def stock_symbols(self, _exchange):
            return SYMBOLS_FIXTURE

        def company_profile2(self, symbol):
            return PROFILES.get(symbol, {})

        def company_basic_financials(self, symbol, _metric):
            return FINANCIALS.get(symbol, {"metric": {}})

        def quote(self, symbol):
            return QUOTES.get(symbol, {})

    with patch.object(finnhub_source, "_client", return_value=FakeClient()):
        kept = finnhub_source.refresh_universe(db_session)

    assert kept == 1
    rows = db_session.query(Stock).all()
    assert len(rows) == 1
    assert rows[0].ticker == "GOOD"
    assert rows[0].market_cap == 50_000 * 1_000_000
    assert rows[0].sector == "Tech"


def test_rate_limiter_throttles_when_window_full(monkeypatch):
    monkeypatch.setattr(finnhub_source, "MAX_CALLS_PER_MINUTE", 3)

    sleeps: list[float] = []
    monkeypatch.setattr(finnhub_source.time, "sleep", lambda s: sleeps.append(s))

    @finnhub_source._rate_limited
    def noop():
        return 1

    for _ in range(4):
        noop()

    assert len(sleeps) == 1
    assert sleeps[0] > 0
