from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(256))
    sector: Mapped[str | None] = mapped_column(String(128))
    market_cap: Mapped[float | None] = mapped_column(Float)
    avg_volume: Mapped[float | None] = mapped_column(Float)
    next_earnings: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    quotes: Mapped[list["Quote"]] = relationship(back_populates="stock")
    news: Mapped[list["NewsItem"]] = relationship(back_populates="stock")
    analyst_actions: Mapped[list["AnalystAction"]] = relationship(back_populates="stock")
    filings: Mapped[list["Filing"]] = relationship(back_populates="stock")
    contracts: Mapped[list["Contract"]] = relationship(back_populates="stock")
    scores: Mapped[list["Score"]] = relationship(back_populates="stock")


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    price: Mapped[float] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float)

    stock: Mapped[Stock] = relationship(back_populates="quotes")


class NewsItem(Base):
    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    headline: Mapped[str] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(128))
    url: Mapped[str | None] = mapped_column(Text)
    sentiment: Mapped[float | None] = mapped_column(Float)

    stock: Mapped[Stock] = relationship(back_populates="news")


class AnalystAction(Base):
    __tablename__ = "analyst_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    firm: Mapped[str | None] = mapped_column(String(128))
    action: Mapped[str | None] = mapped_column(String(64))
    rating: Mapped[str | None] = mapped_column(String(64))
    price_target: Mapped[float | None] = mapped_column(Float)

    stock: Mapped[Stock] = relationship(back_populates="analyst_actions")


class Filing(Base):
    __tablename__ = "filings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    type: Mapped[str] = mapped_column(String(32))
    url: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)

    stock: Mapped[Stock] = relationship(back_populates="filings")


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    agency: Mapped[str | None] = mapped_column(String(128))
    amount: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(Text)

    stock: Mapped[Stock] = relationship(back_populates="contracts")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stock_id: Mapped[int] = mapped_column(ForeignKey("stocks.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    watchlist_score: Mapped[float | None] = mapped_column(Float)
    trigger_score: Mapped[float | None] = mapped_column(Float)
    signals_json: Mapped[str | None] = mapped_column(Text)

    stock: Mapped[Stock] = relationship(back_populates="scores")


class MacroSnapshot(Base):
    __tablename__ = "macro_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    spy_price: Mapped[float | None] = mapped_column(Float)
    qqq_price: Mapped[float | None] = mapped_column(Float)
    vix: Mapped[float | None] = mapped_column(Float)
    ten_year_yield: Mapped[float | None] = mapped_column(Float)
    dxy: Mapped[float | None] = mapped_column(Float)
    regime_score: Mapped[float | None] = mapped_column(Float)
