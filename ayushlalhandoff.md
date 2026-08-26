# Handoff — PortfolioLab (100-investor)

Repo: https://github.com/ayushl13/100-investor
Local path (Aayush's machine): `~/Desktop/100-investor`
App entry point: `app.py` (single-file Streamlit app)

## Collaboration setup

- Owner: ayushl13 (friend, wrote the original `app.py`). Aayush is a collaborator on the GitHub repo.
- Originally shared via VS Code Live Share, but Live Share only gives live streaming access, not a real local copy — the actual workflow is: owner pushes to GitHub, Aayush works on a local clone, commits/pushes back.
- **Hard rule: never add Claude/an AI assistant as a contributor, co-author, or credit anywhere in this repo** (commit trailers, PR descriptions, README, code comments) — explicit standing instruction, applies to every repo, not just this one.

## Stack

- Python 3.9.6, Streamlit 1.50.0, `yfinance` 1.2.0, `pandas` 2.3.3, Altair 5.5.0 (bundled with Streamlit). Exact versions pinned in `requirements.txt` — verified this session by installing them into a brand-new empty venv and confirming the app runs.
- Local dev venv lives at `.venv/` (gitignored, not committed) — see "Getting it running again" below to recreate it.
- `users.json` (local account store, see Authentication below) is gitignored — never gets pushed to GitHub. Each machine running the app builds up its own local `users.json` as people sign up on it.

## Getting it running again (from a fresh clone, fresh session, or your friend's machine)

```bash
cd 100-investor          # inside the cloned repo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL it prints (usually `http://localhost:8501`). That's the whole setup — no API keys, no accounts, no extra config. `.streamlit/config.toml` (already in the repo) applies the dark theme automatically.

## What the app does

Single-page Streamlit app ("PortfolioLab") simulating 3 preset portfolios (Conservative/Moderate/Aggressive) built from VOO/QQQ/VXUS/BND, using real 5-year historical data from Yahoo Finance via `yfinance`. Pages (sidebar radio, not real URLs — it's one script): Overview, Portfolio, Performance, Risk, ETF Research, Scenario Lab, About.

## What changed this session

1. **Dark theme + animated background** — `.streamlit/config.toml` sets a dark theme (bg `#161618`, accent blue `#4A9EFF`). `app.py` injects a canvas-based "kinetic grid" animated background (ported from a React/Tailwind component the user had, translated to vanilla JS since this is Streamlit, not React) via `st.components.v1.html`. It tries real cursor-tracking by reaching into `window.parent` (works if the browser allows same-origin iframe access) and falls back to an ambient auto-animated version if that's blocked — this fallback exists because Streamlit's `components.html` runs in a sandboxed iframe and cross-frame access isn't guaranteed across browsers.
2. **Chart y-axis fix (real bug)** — Streamlit's default `st.line_chart`/`st.area_chart` anchor the y-axis at 0, which flattens high-priced tickers (e.g. a $700 VOO chart looks like a straight line). Replaced every price/value line chart with custom Altair charts (`line_chart_single` / `line_chart_multi` helper functions, defined near the top of `app.py`) using `scale=alt.Scale(zero=False)`. Left the Allocation Breakdown **bar chart** and the Risk page's **drawdown chart** zero-anchored on purpose — that's the statistically correct way to show a proportion/percentage, not an oversight.
3. **Click-to-view stock detail popup** — `ticker_dialog(ticker)` (a real `st.dialog` modal) shows Day/Week/Month/Year/YTD tabs (line charts) plus key stats (price, day range, 52-week range, market cap or volume) pulled from `yf.Ticker(ticker).fast_info` and `.history()`, both wrapped in `@st.cache_data(ttl=300)`. Triggered via `ticker_button()`, a thin wrapper around `st.button(..., type="tertiary")` so it renders as plain clickable text rather than a boxed button.
   - Wired up in: Overview page's allocation list, Portfolio page's "What You Own" section (the ticker **name itself** is the click target here — no separate button), and the ETF Research page.
   - The Portfolio page's **Holdings table** was deliberately reverted to a plain `st.dataframe` (no buttons) after going back and forth — the user wanted click-to-view consolidated only in "What You Own," and wanted Holdings to just be a clean, seamless grid.
4. **Portfolio page additions**: a new "Portfolio Value" line chart was added above "Allocation Breakdown" (plain line, not filled — user explicitly didn't want it filled). "What You Own" now has real 1–2 sentence descriptions per ETF (added to the `etf_information` dict as a `"description"` field) in bright white text, sized larger than the role/focus blurb underneath (light blue, smaller).
5. **Sign up / sign in (real feature, not decorative)** — the whole app is now gated behind an auth screen (`render_auth_screen()`), ported from a React/shadcn component the user had into native Streamlit widgets (the original was TSX, not usable directly). Accounts are stored locally in `users.json` — email → `{name, salt, password_hash}` — hashed with `hashlib.pbkdf2_hmac`, never plaintext. `create_user()` / `authenticate()` handle signup/login; both were unit-tested this session in isolation (duplicate-email rejection, wrong-password rejection, hash never contains the raw password). The "Continue with Google" button from the reference was deliberately dropped — real Google OAuth needs API credentials nobody has, so a fake button would violate "make sure it works." Sidebar shows "Signed in as X" + a Log Out button once authenticated.
6. **Password strength meter** — 4-tier bar (length/uppercase/number/special-char) + checklist, ported from the same reference. Two layers: a static Python-rendered version (`render_password_strength_meter`, updates on Enter/blur — always works) and an attempted **live**, updates-per-keystroke version (`render_live_password_strength_script`) that reaches into the real page via the same `window.parent` trick as the background — if the browser allows it, it hides the static meter and takes over instantly; if blocked, the static one silently remains. Never confirmed which mode actually engages in the user's Safari.
7. **Hid Streamlit's native "Press Enter to apply" hint** (`[data-testid="InputInstructions"]`) globally via injected CSS — was cluttering the auth forms and is redundant with the live meter attempt.
8. **Add custom stocks to your portfolio (major architecture change)** — previously the portfolio was *only* `{ticker: weight}` from the 3 presets. Now:
   - `st.session_state["custom_holdings"]` holds `{ticker: dollar_amount}` for anything the user manually adds.
   - The "SELECT PORTFOLIO" section (near the top of `app.py`) merges preset-derived dollar amounts (`weight * amount`) with `custom_holdings` (summed if the same ticker appears in both), then re-normalizes into `portfolio` as weights — so every downstream calculation that already expected `portfolio = {ticker: weight}` kept working unchanged.
   - **`amount` (the sidebar base investment) is no longer what's shown/charted anywhere except as an input to the preset.** A new `total_invested` (sum of all combined dollar holdings, preset + custom) replaced `amount` in every metric, chart, and calculation across Overview/Portfolio/Performance/ETF Research. If you add code that touches money amounts, use `total_invested`, not `amount`.
   - New "Add a Stock" section on the Portfolio page (`render_add_stock_section()`): a live-fetched, cached (24h) list of all ~503 current S&P 500 companies pulled from Wikipedia (`fetch_sp500_list()`, with a 10-company hardcoded fallback if that fetch ever fails), a sector multiselect filter (real GICS sectors: Info Tech, Health Care, Financials, etc. — checking multiple sectors shows the union, not intersection), a stock+amount picker, and a list of currently-added stocks each with a Remove button.
   - Custom-added tickers (not one of the 4 hardcoded ETFs) get their company name/sector/description fetched live via `yf.Ticker(ticker).info` (`fetch_company_info()`, cached 1h, with a generic fallback if the fetch fails) instead of the hardcoded `etf_information` dict — accessed everywhere via the safe `get_ticker_display_info(ticker)` helper instead of direct dict indexing, so custom stocks show up correctly in "What You Own," the ticker detail popup, and the ETF Research page selector (which now lists every current holding, not just the 4 presets).
   - Verified end-to-end this session using a throwaway scratch copy of the app with the login gate bypassed and 2 fake custom holdings (AAPL, JNJ) pre-seeded — confirmed the whole pipeline (data download, Holdings table, Add a Stock section, Portfolio Value chart, Allocation Breakdown, What You Own with live-fetched company info) runs with no errors. The scratch copy was deleted after testing, never committed.

## Known issues carried over from the original code (not yet fixed, flagged for the user)

- **No caching on the original `yf.download()` calls** (the ones from before this session, at the top of the script and in ETF Research / Scenario Lab) — every widget interaction re-downloads 5 years of data. Only the ticker-dialog and company-info fetches added this session are cached.
- **No error handling** around those original `yf.download()` calls — a Yahoo Finance hiccup will crash the whole app with a raw traceback.
- **Hardcoded fragile dependency**: `benchmark_returns = returns["VOO"]` assumes VOO is always in whatever preset is selected. True for all 3 current presets (custom-added stocks only add on top, they can't remove VOO), but would break if a portfolio without VOO were ever added.
- Streamlit deprecation warning in the logs about `use_container_width` (harmless for now, will need updating before Streamlit removes it after 2025-12-31).
- **New this session**: `fetch_sp500_list()` scrapes Wikipedia's S&P 500 page structure — if Wikipedia ever changes that table's column names/layout, the fetch will fail and silently fall back to the tiny 10-company `SP500_FALLBACK` list. Not a crash, just a degraded "every stock" list until noticed.
- **New this session**: `fetch_company_info()` calls `yf.Ticker(ticker).info`, which is a slower/heavier yfinance call than `.fast_info` — fine for occasional use (adding a stock, viewing "What You Own") but would need caching/rate-limit awareness if this pattern gets reused somewhere called more frequently.

## Suggested next steps

- Add `@st.cache_data` to the original top-of-script `yf.download()` calls and wrap them in try/except.
- Decide whether to extend click-to-view ticker popups to any other spots on the site.
- Confirm whether the live per-keystroke password meter and live cursor-tracking background actually engage in the user's browser, or are silently falling back — never got a definitive answer either way this session.
- User mentioned wanting to "wire more in later" on the custom-stock feature — nothing specific was requested yet beyond what's built.
