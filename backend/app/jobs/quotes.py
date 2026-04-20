import logging
from datetime import datetime

from app.db import SessionLocal
from app.models import Quote, Stock
from app.sources import finnhub as finnhub_source
from app.sources import yfinance_source

logger = logging.getLogger(__name__)


def refresh_universe_job() -> None:
    logger.info("Starting universe refresh job")
    session = SessionLocal()
    try:
        finnhub_source.refresh_universe(session)
    except Exception:
        logger.exception("Universe refresh failed")
        session.rollback()
    finally:
        session.close()


def refresh_quotes_job() -> None:
    session = SessionLocal()
    try:
        tickers = [t for (t,) in session.query(Stock.ticker).all()]
        if not tickers:
            logger.info("No stocks in universe; skipping quote refresh")
            return
        logger.info("Refreshing quotes for %d tickers", len(tickers))
        quotes = yfinance_source.fetch_batch_quotes(tickers)
        stock_ids = {t: sid for sid, t in session.query(Stock.id, Stock.ticker).all()}
        rows = []
        for ticker, q in quotes.items():
            sid = stock_ids.get(ticker)
            if sid is None or q.get("price") is None:
                continue
            rows.append(Quote(
                stock_id=sid,
                timestamp=q.get("timestamp") or datetime.utcnow(),
                price=q["price"],
                volume=q.get("volume"),
            ))
        session.add_all(rows)
        session.commit()
        logger.info("Inserted %d quote rows", len(rows))
    except Exception:
        logger.exception("Quote refresh failed")
        session.rollback()
    finally:
        session.close()
