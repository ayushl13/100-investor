# PortfolioLab

**Want to open the site?**

Since you already have the project on your computer: go to VS Code and hit File → Open Folder, and open the folder of whatever this project is called on your computer (mine is called `100-investor`). Then open a new terminal inside that window (Terminal → New Terminal in the menu bar).

Before pasting anything, type `pwd` and press Enter to make sure you're in the right folder — it should end in your project's name (e.g. `.../100-investor`). Then paste the following:

```bash
git pull origin main
pip install -r requirements.txt
streamlit run app.py
```

Never cloned it before (first time on this machine)? Open any terminal and paste this instead — it'll create the folder for you:

```bash
git clone https://github.com/ayushl13/100-investor.git
cd 100-investor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Either way, it'll open automatically in your browser (usually `http://localhost:8501`).

**One-time extra step for the Scenario Lab (trading arena) to work:** the leaderboard/challenges are shared between everyone using the app, backed by a real database. Create a file at `.streamlit/secrets.toml` inside the project folder (this file is gitignored — it never gets pushed to GitHub, and you'll never see it after pulling) with this content:

```toml
DATABASE_URL = "ask Aayush for this connection string directly (text/DM, not GitHub)"
```

Without this file, every page except Scenario Lab works fine — Scenario Lab specifically needs it.

## What it does

- Sign up / sign in to use it (accounts are stored locally, passwords are hashed — never saved in plain text; staying signed in survives a page reload)
- Pick a portfolio (Conservative, Moderate, Aggressive) made of a few ETFs — VOO, QQQ, VXUS, BND
- Add your own individual stocks on top of that, picked from the full current S&P 500 list, filterable by sector
- See how much your money would've grown historically, compared against the S&P 500
- Look at risk stuff: volatility, max drawdown, a simplified risk score
- Click into any ticker (ETF or stock you added) to see its price chart (day/week/month/year/YTD) plus key stats
- **Scenario Lab is a full trading simulator**: start with $100,000 in virtual cash, buy/sell real stocks at live prices, track your portfolio's growth over time, compete on a shared leaderboard, and complete daily/weekly challenges for bonus points and cash

Everything is historical simulation — not investment advice, just a way to learn.

## Stack

- Python + Streamlit for the app/UI
- `yfinance` for pulling real historical price data
- `pandas` for the return/growth math
- Altair for the charts (so the y-axis actually zooms into price movement instead of flattening everything to zero)
- A live-fetched, cached list of S&P 500 companies (pulled from Wikipedia) powers the "add a stock" dropdown
- Postgres (Neon, shared/hosted) backs the Scenario Lab trading engine — accounts, holdings, trades, and challenges live there so the leaderboard is shared across everyone running the app

## Why

Wanted a low-stakes way to poke at real market data and actually see how allocation decisions play out, rather than just trusting a rule of thumb. Still very much a work in progress.
