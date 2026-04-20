# Stock Signal App

A personal-use web app that surfaces the highest-signal US stocks each day via two auto-populated lists: a **Watchlist** (stocks with building setup momentum) and a **Buy Now** list (stocks with fresh trigger events). Single-user, self-hosted, dark mode web UI.

## Tech stack

- **Backend:** Python 3.11+, FastAPI, SQLite, SQLAlchemy, APScheduler
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui (dark mode default)
- **Data sources (all free):** Finnhub, yfinance, SEC EDGAR, FRED, USAspending.gov

## Key docs

- `PRD.md` — full product specification. Read this when working on any feature.
- `ROADMAP.md` — ordered build phases with checklist. Follow in order, top to bottom.

## Project structure

```
stock-signal-app/
├── CLAUDE.md
├── PRD.md
├── ROADMAP.md
├── README.md
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entry
│   │   ├── scheduler.py      # APScheduler jobs
│   │   ├── db.py             # SQLite + SQLAlchemy setup
│   │   ├── models.py         # ORM models
│   │   ├── sources/          # Data source integrations
│   │   │   ├── finnhub.py
│   │   │   ├── yfinance.py
│   │   │   ├── sec_edgar.py
│   │   │   ├── fred.py
│   │   │   └── usaspending.py
│   │   ├── scoring/          # Scoring logic
│   │   │   ├── watchlist.py
│   │   │   ├── trigger.py
│   │   │   └── regime.py
│   │   └── api/              # FastAPI routes
│   │       ├── watchlist.py
│   │       ├── buy_now.py
│   │       ├── stock_detail.py
│   │       └── macro.py
│   └── requirements.txt
└── frontend/
    ├── app/
    │   ├── page.tsx          # Main dashboard
    │   └── layout.tsx
    ├── components/
    │   ├── macro-panel.tsx
    │   ├── buy-now-list.tsx
    │   ├── watchlist.tsx
    │   ├── stock-detail.tsx
    │   └── ui/               # shadcn components
    ├── lib/
    │   └── api.ts
    └── package.json
```

## Conventions

- **Python:** type hints everywhere, Black formatter, Pytest for tests, Pydantic for request/response models
- **TypeScript:** strict mode, shadcn/ui for all UI components (avoid custom CSS where possible)
- **Commit style:** Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`, `docs:`)
- **Secrets:** API keys in `.env` (never commit), accessed via `os.getenv()` or `process.env`
- **Timestamps:** store as UTC in DB; display in user local time on frontend
- **File size:** one module = one responsibility; keep files small and focused

## Important constraints

- **Single-user app** — no authentication, no multi-tenant logic, no user accounts
- **Free API tiers only for MVP** — respect rate limits (Finnhub free tier: 60 calls/min)
- **No websockets for MVP** — HTTP polling is fine (5-minute refresh during market hours)
- **Stock universe** = ~1,000 most liquid US equities (market cap > $2B, ADV > $50M), refreshed weekly
- **No penny stocks, no OTC, no ADRs** initially

## Execution rules (for Claude Code)

- Work on **one ROADMAP phase at a time**. Do not scope creep.
- Before implementing anything, **check PRD.md** for exact specs (scoring formulas, thresholds, refresh schedules).
- When a phase is complete, **update ROADMAP.md** (check the box) before starting the next.
- If unsure about a product decision, **ask the user** rather than guess.
- Prefer **editing existing files** over creating new ones unless the structure clearly demands it.
- Always add new dependencies to `requirements.txt` or `package.json` with pinned versions.
- Write at least smoke tests for each backend module (data fetching + scoring).
