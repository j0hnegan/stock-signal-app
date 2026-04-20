from datetime import datetime

import pandas as pd

from app.sources import yfinance_source


def _multi_ticker_frame(tickers: list[str]) -> pd.DataFrame:
    idx = pd.DatetimeIndex([datetime(2026, 4, 20, 14, 0), datetime(2026, 4, 20, 14, 5)])
    cols = pd.MultiIndex.from_product([tickers, ["Open", "High", "Low", "Close", "Volume"]])
    data = {}
    for t in tickers:
        for field, val in [("Open", 1.0), ("High", 1.1), ("Low", 0.9), ("Close", 1.05), ("Volume", 1000.0)]:
            data[(t, field)] = [val, val + 0.01]
    return pd.DataFrame(data, index=idx, columns=cols)


def test_fetch_batch_quotes_returns_latest_per_ticker(monkeypatch):
    tickers = ["AAPL", "MSFT"]
    monkeypatch.setattr(yfinance_source.yf, "download", lambda *a, **kw: _multi_ticker_frame(tickers))

    result = yfinance_source.fetch_batch_quotes(tickers)

    assert set(result.keys()) == {"AAPL", "MSFT"}
    for t in tickers:
        assert result[t]["price"] == pytest_approx(1.06)
        assert result[t]["volume"] == pytest_approx(1000.01)
        assert isinstance(result[t]["timestamp"], datetime)


def test_fetch_batch_quotes_empty_input():
    assert yfinance_source.fetch_batch_quotes([]) == {}


def test_fetch_batch_quotes_swallows_errors(monkeypatch):
    def boom(*_a, **_kw):
        raise RuntimeError("network down")

    monkeypatch.setattr(yfinance_source.yf, "download", boom)
    assert yfinance_source.fetch_batch_quotes(["AAPL"]) == {}


def pytest_approx(value: float, tol: float = 1e-6):
    class _Approx:
        def __eq__(self, other):
            return abs(other - value) < tol
        def __repr__(self):
            return f"~{value}"
    return _Approx()
