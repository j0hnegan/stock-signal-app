# Stock Signal App

A personal-use, single-user web app that auto-populates two lists of US stocks each day: a **Watchlist** of stocks building setup momentum and a **Buy Now** list of stocks with fresh trigger events. Dark mode dashboard, no auth, self-hosted.

See [`PRD.md`](PRD.md) for the full product spec and [`ROADMAP.md`](ROADMAP.md) for the build plan.

## Tech stack

- **Backend:** Python 3.11+, FastAPI, SQLite + SQLAlchemy, APScheduler
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind, shadcn/ui
- **Data:** Finnhub, yfinance, SEC EDGAR, FRED, USAspending.gov (all free tiers)

## Local setup

```bash
git clone <repo-url> stock-signal-app
cd stock-signal-app
cp .env.example .env   # then fill in your API keys
```

### Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check: <http://localhost:8000/health>

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: <http://localhost:3000>

## Environment variables

| Variable | Source | Notes |
|---|---|---|
| `FINNHUB_API_KEY` | <https://finnhub.io> | Free tier: 60 calls/min |
| `FRED_API_KEY` | <https://fred.stlouisfed.org/docs/api/api_key.html> | Free, no practical limit |

## Deployment

Deferred to Phase 8 — see [`ROADMAP.md`](ROADMAP.md).
