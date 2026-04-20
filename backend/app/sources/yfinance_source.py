import logging
from datetime import datetime
from typing import Any

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

BATCH_SIZE = 200


def fetch_history(ticker: str, period: str = "1y") -> pd.DataFrame:
    try:
        return yf.Ticker(ticker).history(period=period, auto_adjust=False)
    except Exception as exc:
        logger.warning("yfinance history failed for %s: %s", ticker, exc)
        return pd.DataFrame()


def fetch_batch_quotes(tickers: list[str]) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    if not tickers:
        return results

    for start in range(0, len(tickers), BATCH_SIZE):
        chunk = tickers[start:start + BATCH_SIZE]
        try:
            df = yf.download(
                chunk,
                period="1d",
                interval="5m",
                group_by="ticker",
                threads=True,
                progress=False,
                auto_adjust=False,
            )
        except Exception as exc:
            logger.warning("yfinance batch download failed for chunk starting %s: %s", chunk[0], exc)
            continue

        if df.empty:
            continue

        for ticker in chunk:
            try:
                if len(chunk) == 1:
                    sub = df
                else:
                    sub = df[ticker] if ticker in df.columns.get_level_values(0) else None
                if sub is None or sub.empty:
                    continue
                sub = sub.dropna(subset=["Close"])
                if sub.empty:
                    continue
                last = sub.iloc[-1]
                ts = sub.index[-1]
                results[ticker] = {
                    "price": float(last["Close"]),
                    "volume": float(last["Volume"]) if pd.notna(last.get("Volume")) else None,
                    "timestamp": ts.to_pydatetime() if hasattr(ts, "to_pydatetime") else datetime.fromtimestamp(ts),
                }
            except Exception as exc:
                logger.debug("parse failed for %s: %s", ticker, exc)
                continue

    return results
