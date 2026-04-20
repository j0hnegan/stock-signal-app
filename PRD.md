# Product Requirements Document: Stock Signal App (MVP)

## 1. Overview

A personal-use web app that auto-populates two lists of US stocks based on real-time signals:

- **Watchlist** — stocks building setup momentum over the past 5–20 trading days
- **Buy Now** — stocks with fresh trigger events in the last 24 hours

Built for single-user, self-hosted deployment. Dark mode web UI. No authentication.

## 2. Goal

Replace manual chart-watching and news-scanning with an always-on radar that surfaces the 5–15 highest-signal stocks per day from a universe of ~1,000 liquid US equities. The user makes the buy decisions; the app ensures no actionable setup is missed.

## 3. User stories

- As the user, I open the app and immediately see which stocks I should pay attention to today.
- As the user, I can click any stock to see exactly *why* it scored — which signals fired, what the news is, what the chart looks like.
- As the user, I see at the top whether the overall market is in a favorable, neutral, or unfavorable regime.
- As the user, I never have to manually add stocks to any list — the app decides what matters.
- As the user, I see stocks that were pre-validated by the Watchlist *and* surprise rippers from unwatched names, both in the Buy Now list.

## 4. Tech stack

| Layer | Technology |
|---|---|
| Backend language | Python 3.11+ |
| Backend framework | FastAPI |
| Scheduler | APScheduler (inside FastAPI process) |
| Database | SQLite (MVP), migrate to Postgres later |
| ORM | SQLAlchemy |
| Frontend framework | Next.js 14 (App Router) |
| Frontend language | TypeScript (strict mode) |
| Styling | Tailwind CSS |
| UI components | shadcn/ui (dark mode default) |
| Charts | Recharts or TradingView lightweight-charts |
| Hosting (later) | Railway (backend), Vercel (frontend), or DigitalOcean droplet |

## 5. Data sources (all free for MVP)

| Source | Purpose | Endpoint / library |
|---|---|---|
| **Finnhub API** | News headlines, analyst ratings, earnings calendar, fundamentals, quotes | `finnhub.io/api/v1/*` |
| **yfinance** | Historical prices, volume, backup for quotes and earnings dates | `yfinance` Python library |
| **SEC EDGAR** | 8-K filings (material events), Form 4 (insider trades) | `data.sec.gov/submissions` |
| **FRED API** | Macro data (VIX, 10Y yield, DXY, SPY, QQQ via series) | `api.stlouisfed.org/fred` |
| **USAspending.gov API** | Federal contract awards (DARPA, DoD, DoE, etc.) | `api.usaspending.gov/api/v2` |

### Rate limits and respect

- **Finnhub free:** 60 calls/minute — use wisely; batch where possible
- **SEC EDGAR:** 10 requests/second max; include a descriptive `User-Agent` header
- **FRED:** very generous, essentially no limit for personal use
- **USAspending:** public, no auth, rate-limit by respect
- **yfinance:** unofficial, cache aggressively, avoid hammering

## 6. Stock universe

- Starting set: ~1,000 most liquid US equities
- Filters: market cap > $2B, average daily dollar volume > $50M
- Exclusions: OTC, ADRs (initially), any stock under $5/share
- Fetched once at setup (from Finnhub `/stock/symbol` + fundamentals filter)
- Refreshed every Sunday at 6:00 AM ET

## 7. Core features

### 7.1 Watchlist (auto-populated)

Stocks with building setup momentum over the last 5–20 trading days. Appear when **Watchlist Score ≥ 60**.

**Watchlist Score components (0–100):**

| Signal | Weight |
|---|---|
| Recent analyst upgrades/initiations (last 10 days, +20 per, cap 40) | up to +40 |
| Rising analyst consensus (price target increases last 30 days) | +10 |
| Relative strength vs. SPY over 20 days (scaled) | +0–20 |
| Earnings in next 14 days | +10 |
| Sector in top 3 performing sectors this week | +15 |
| Volume trending above 20-day average | +10 |
| Insider buying in last 10 days (Form 4, net positive) | +15 |

**Display per row:**
- Ticker + company name
- Current Watchlist Score (0–100, color gradient)
- Top 2 contributing signals as badges
- 7-day price sparkline
- Tap/click opens Stock Detail view

### 7.2 Buy Now list (auto-populated)

Stocks with a fresh trigger event. Appear when:

- **Trigger Score ≥ 50** (standalone), OR
- **Trigger Score ≥ 35** if also on the Watchlist (pre-validated → lower bar)

**Trigger Score components (0–100):**

| Signal | Weight |
|---|---|
| Analyst initiation or upgrade today | +40 |
| Large price target raise (>15% increase) | +30 |
| M&A headline or 8-K material event | +40 |
| DARPA / major federal contract award (USAspending) | +35 |
| Price gap-up >3% on 2x+ average volume | +30 |
| Breaking news with bullish keywords, ticker tagged | +20 |
| Ecosystem ripple (e.g., NVDA announcement → quantum names) | +15 |

**Display per row:**
- Ticker + company name
- Trigger Score
- **One-line explanation of trigger** (e.g., "Jefferies initiated Buy, $175 PT")
- Timestamp (relative, "12 min ago")
- Badge:
  - 🎯 **Pre-setup** if also on Watchlist
  - ⚡ **Surprise** if trigger fired on an unwatched name

**Expiry:** auto-remove from Buy Now list 3 days after trigger fires (configurable).

### 7.3 Stock Detail view

Opens as a drawer or full-page route when a stock is clicked in either list.

**Contents:**
- Current price, day change %, volume vs. 20-day average
- **Watchlist Score breakdown** — each contributing factor with its weight
- **Trigger Score breakdown** — each contributing factor (if applicable)
- Recent headlines (last 14 days, clickable to source)
- Recent analyst actions (rating changes, PT changes)
- Upcoming earnings date
- Price chart with timeframe toggle (1D, 5D, 1M, 6M, 1Y)
- Recent insider transactions (last 30 days)
- "Open in TradingView" external link

### 7.4 Macro Regime Panel (top of dashboard)

Horizontal strip, always visible.

**Displays:**
- **Regime Score** (0–100) with green/yellow/red color band
- SPY: price, 1-day %, position vs. 20-day and 50-day MA
- QQQ: same
- VIX: level + 1-day change
- 10Y Treasury yield: level + 5-day direction
- Today's high-impact economic events (CPI, FOMC, NFP, etc.)

**Regime Score formula (0–100):**

| Condition | Points |
|---|---|
| SPY above both 20-day and 50-day MA | +25 |
| VIX < 20 | +20 |
| Market breadth positive (>55% of universe above 50-day MA) | +15 |
| QQQ outperforming SPY over 5 days (risk-on tech signal) | +15 |
| 10Y yield not rising sharply (< 10bps/week) | +15 |
| No high-impact economic event in next 2 trading days | +10 |

**Color bands:**
- 🟢 Green: ≥ 70
- 🟡 Yellow: 40–69
- 🔴 Red: < 40

The regime does **not** gate trading — it calibrates expectations.

## 8. Data refresh schedule

| Data | During market hours (9:30 AM–4:00 PM ET) | Off hours |
|---|---|---|
| Quotes (price, volume) | every 5 minutes | hourly |
| News + analyst ratings | every 5 minutes | every 30 minutes |
| SEC 8-K / Form 4 | every 15 minutes | every 30 minutes |
| USAspending contracts | every 60 minutes | every 2 hours |
| Earnings calendar | once daily at 6:00 AM ET | — |
| Macro data (FRED) | once daily at 6:00 AM ET | — |
| Universe refresh | Sunday 6:00 AM ET | — |
| Trigger Score recomputation | every 5 minutes | every 30 minutes |
| Watchlist Score recomputation | every hour | every 6 hours |
| Regime Score recomputation | every 15 minutes | hourly |

## 9. UI/UX requirements

- **Dark mode default** (shadcn/ui default dark theme)
- **Single-page dashboard** layout:
  - Top: Macro Regime Panel (horizontal strip, full width)
  - Left column (primary, wider): Buy Now list
  - Right column (secondary, narrower): Watchlist (scrollable)
  - Stock Detail opens as a slide-in drawer from the right
- **No navigation menu** for MVP — just the dashboard
- **Mobile responsive** but **desktop-first**
- **Color coding:**
  - Green for bullish signals and positive scores
  - Red for bearish signals / warnings
  - Yellow/amber for neutral or cautionary
- **Timestamps:** user local time, relative format ("5 min ago", "2 hours ago")
- **Auto-refresh:** entire dashboard re-fetches every 60 seconds

## 10. Out of scope for MVP

- User authentication / multi-user
- Mobile app (web-only)
- Paid data sources (Unusual Whales, Benzinga, Polygon paid tiers)
- Real-time websockets (polling is fine)
- Push notifications / email alerts
- Trade execution / broker integration
- Portfolio tracking
- Backtesting
- Options flow signals
- Social sentiment signals (Stocktwits, WSB, X)
- Congress trading tracker
- Position management / forced trade journal
- Theme filtering UI
- Small-cap / speculative scanner (separate project)

## 11. Success criteria

- Runs for a full trading week without crashing
- Buy Now list surfaces 3–10 actionable stocks per day on average
- At least 60% of Buy Now entries correspond to stocks that moved >2% in the 3 days after triggering
- User reports that the app surfaces at least 1 trade per week they wouldn't have found manually

## 12. Post-MVP roadmap (for reference, not to build now)

- Add paid data sources (Unusual Whales for options flow, Benzinga for faster news)
- Social sentiment signals
- Push notifications (Pushover, Twilio)
- Position management + trade journal (forced thesis entry, auto-exit reminders)
- Theme detection and filtering UI
- Small-cap / speculative scanner as separate view
- Mobile app (React Native or PWA)
- Multi-user (auth, separate databases) — only if productizing
