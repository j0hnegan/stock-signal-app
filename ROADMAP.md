# Build Roadmap

Build phases in order. Complete all tasks in a phase before moving to the next. Check off each task as it's completed.

---

## Phase 0: Project setup

- [x] Create root directory, initialize git repo
- [x] Create `.gitignore` (Python, Node, `.env`, `*.db`, `__pycache__`, `node_modules`)
- [x] Create `.env.example` with placeholder keys for:
  - `FINNHUB_API_KEY`
  - `FRED_API_KEY`
  - ~~`SEC_USER_AGENT`~~ (deferred to Phase 3 when SEC EDGAR integration lands)
- [x] Create `README.md` with setup instructions
- [x] Scaffold `backend/` and `frontend/` directories

---

## Phase 1: Backend skeleton

- [x] Initialize Python project, create `backend/requirements.txt` with: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `apscheduler`, `pydantic`, `python-dotenv`, `httpx`, `yfinance`, `finnhub-python`, `pytest`
- [x] Create `backend/app/main.py` — FastAPI app with health-check endpoint `/health`
- [x] Create `backend/app/db.py` — SQLite setup with SQLAlchemy engine + session
- [x] Create `backend/app/models.py` — define core models:
  - `Stock` (ticker, name, sector, market_cap, avg_volume)
  - `Quote` (stock_id, timestamp, price, volume)
  - `NewsItem` (stock_id, timestamp, headline, source, url, sentiment)
  - `AnalystAction` (stock_id, timestamp, firm, action, rating, price_target)
  - `Filing` (stock_id, timestamp, type, url, summary)
  - `Contract` (stock_id, timestamp, agency, amount, description)
  - `Score` (stock_id, timestamp, watchlist_score, trigger_score, signals_json)
  - `MacroSnapshot` (timestamp, spy_price, qqq_price, vix, ten_year_yield, regime_score)
- [x] Create `backend/app/scheduler.py` — APScheduler setup with empty job registry
- [x] Wire scheduler startup/shutdown into FastAPI lifespan
- [x] Verify: running `uvicorn app.main:app --reload` starts cleanly; `/health` returns OK

---

## Phase 2: Data sources — universe and prices

- [x] Create `backend/app/sources/finnhub.py`:
  - Fetch US stock universe (`/stock/symbol?exchange=US`)
  - Filter to market cap > $2B and ADV > $50M (using `/stock/profile2` and `/stock/metric`)
  - Function: `refresh_universe()` — populates `Stock` table
  - Function: `fetch_quote(ticker)` — returns current price + volume *(Finnhub `/quote` doesn't include volume on free tier — volume comes from yfinance batch path)*
- [x] Create `backend/app/sources/yfinance_source.py` *(named with `_source` suffix to avoid shadowing the `yfinance` package)*:
  - Function: `fetch_history(ticker, period)` — returns historical OHLCV DataFrame
  - Function: `fetch_batch_quotes(tickers)` — efficient bulk quote (chunked at 200)
- [x] Add scheduled jobs:
  - ~~Universe refresh — weekly Sunday 6 AM ET~~ → **manual-only via `POST /admin/refresh-universe`**; weekly cron dropped (universe barely changes; refresh costs 2–3 hours of free-tier API calls)
  - Quote refresh — every 5 minutes during market hours (+ hourly off-hours)
- [x] Unit tests for each source module (mock HTTP responses)
- [x] Verify: after manual trigger, `Stock` table has ~1,000 rows; `Quote` table populates every 5 min *(structurally verified — endpoint returns `started`, job runs and logs correctly with empty universe; full verification pending real `FINNHUB_API_KEY`)*

---

## Phase 3: Data sources — news, analyst, filings, contracts, macro

- [ ] `backend/app/sources/finnhub.py` (extend):
  - Function: `fetch_company_news(ticker, from_date, to_date)` — populates `NewsItem`
  - Function: `fetch_analyst_ratings(ticker)` — populates `AnalystAction`
  - Function: `fetch_earnings_calendar(from_date, to_date)` — updates `Stock.next_earnings`
- [ ] Create `backend/app/sources/sec_edgar.py`:
  - Function: `fetch_recent_8k(ticker)` — parse RSS/Atom feed for 8-K filings
  - Function: `fetch_form_4(ticker)` — parse insider transactions
  - Populate `Filing` table with appropriate metadata
- [ ] Create `backend/app/sources/usaspending.py`:
  - Function: `fetch_recent_contracts(since)` — pull federal contract awards
  - Match to tickers by recipient name (fuzzy match)
  - Populate `Contract` table
- [ ] Create `backend/app/sources/fred.py`:
  - Function: `fetch_macro_snapshot()` — pull SPY, QQQ, VIX, 10Y yield, DXY
  - Populate `MacroSnapshot` table
- [ ] Add scheduled jobs per refresh schedule in PRD section 8
- [ ] Unit tests per source
- [ ] Verify: running 30 minutes populates all tables with recent data

---

## Phase 4: Scoring engine

- [ ] Create `backend/app/scoring/watchlist.py`:
  - Function: `compute_watchlist_score(stock) -> (score, signal_breakdown)`
  - Implement all 7 components from PRD section 7.1
  - Return score and JSON breakdown of contributing signals
- [ ] Create `backend/app/scoring/trigger.py`:
  - Function: `compute_trigger_score(stock) -> (score, signal_breakdown, explanation)`
  - Implement all 7 components from PRD section 7.2
  - Return score, breakdown, and one-line explanation for the top trigger
- [ ] Create `backend/app/scoring/regime.py`:
  - Function: `compute_regime_score() -> (score, color, breakdown)`
  - Implement all 6 components from PRD section 7.4
- [ ] Add scheduled jobs:
  - Trigger Score recompute — every 5 minutes
  - Watchlist Score recompute — every hour
  - Regime Score recompute — every 15 minutes
- [ ] Unit tests for scoring logic with fixture data
- [ ] Verify: `Score` table populates; thresholds produce non-empty lists

---

## Phase 5: API endpoints

- [ ] Create `backend/app/api/watchlist.py`:
  - `GET /api/watchlist` — returns stocks with score ≥ 60, ranked desc
  - Response shape: `[{ticker, name, score, top_signals[], sparkline[]}]`
- [ ] Create `backend/app/api/buy_now.py`:
  - `GET /api/buy-now` — returns stocks with trigger conditions met (see PRD 7.2)
  - Include `is_pre_setup` boolean (was on Watchlist)
  - Response shape: `[{ticker, name, score, explanation, timestamp, is_pre_setup}]`
- [ ] Create `backend/app/api/stock_detail.py`:
  - `GET /api/stocks/{ticker}` — full detail: scores, breakdowns, news, analyst, filings, chart data
- [ ] Create `backend/app/api/macro.py`:
  - `GET /api/macro` — current regime score + breakdown + key indicator values
- [ ] CORS middleware to allow frontend origin
- [ ] API integration tests
- [ ] Verify: `curl http://localhost:8000/api/buy-now` returns valid JSON

---

## Phase 6: Frontend scaffold

- [ ] Initialize Next.js 14 app in `frontend/` with TypeScript + Tailwind
- [ ] Install and configure shadcn/ui (dark mode default)
- [ ] Install Recharts
- [ ] Create `frontend/lib/api.ts` — typed client for backend endpoints
- [ ] Create `frontend/app/layout.tsx` — dark-mode root layout
- [ ] Create `frontend/app/page.tsx` — main dashboard shell with three regions:
  - Top: Macro Panel placeholder
  - Left: Buy Now placeholder
  - Right: Watchlist placeholder
- [ ] Verify: `npm run dev` shows empty dashboard shell at `localhost:3000`

---

## Phase 7: Frontend components

- [ ] `components/macro-panel.tsx`:
  - Fetch `/api/macro`, display regime score with color band
  - Show SPY, QQQ, VIX, 10Y yield tiles with price + 1-day change
  - Show today's economic events strip
- [ ] `components/buy-now-list.tsx`:
  - Fetch `/api/buy-now`
  - Render list of cards with ticker, score, explanation, timestamp, pre-setup badge
  - Click opens Stock Detail drawer
- [ ] `components/watchlist.tsx`:
  - Fetch `/api/watchlist`
  - Render compact list with ticker, score, top signals, mini sparkline
  - Click opens Stock Detail drawer
- [ ] `components/stock-detail.tsx` (shadcn Sheet/Drawer):
  - Fetch `/api/stocks/{ticker}`
  - Display: price header, Watchlist and Trigger score breakdowns, recent news, analyst actions, upcoming earnings, price chart (Recharts), recent insider trades, external TradingView link
- [ ] Auto-refresh entire dashboard every 60 seconds
- [ ] Loading skeletons and error states for each component
- [ ] Verify: full dashboard works end-to-end with live data

---

## Phase 8: Polish and deploy

- [ ] Add logging throughout backend (structured JSON logs)
- [ ] Add simple rate-limit guard in each source module (back off on 429)
- [ ] Test full app for one market session, fix bugs
- [ ] Tune score thresholds based on observed output (update in PRD if changed)
- [ ] Write deployment guide in `README.md`
- [ ] Deploy:
  - Backend to Railway (free tier) or Fly.io
  - Frontend to Vercel
  - Set production env variables
- [ ] Verify: live app accessible from phone/laptop, polls correctly

---

## Phase 9 (optional): First post-MVP additions

- [ ] Forced trade-entry journal: when user clicks "I'm taking this trade," prompt for thesis + stop + target
- [ ] Position tracker with time-based exit reminders
- [ ] Better news NLP (OpenAI API or local model for sentiment + ticker extraction beyond what Finnhub provides)
- [ ] Theme detection (cluster news by topic, show running themes panel)
- [ ] Push notifications via Pushover or Expo
