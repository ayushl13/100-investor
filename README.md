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

## What it does

- Sign up / sign in to use it (accounts are stored locally, passwords are hashed — never saved in plain text)
- Pick a portfolio (Conservative, Moderate, Aggressive) made of a few ETFs — VOO, QQQ, VXUS, BND
- Add your own individual stocks on top of that, picked from the full current S&P 500 list, filterable by sector
- See how much your money would've grown historically, compared against the S&P 500
- Look at risk stuff: volatility, max drawdown, a simplified risk score
- Click into any ticker (ETF or stock you added) to see its price chart (day/week/month/year/YTD) plus key stats
- Run a "what-if" scenario with a different amount/risk profile without messing with your main settings

Everything is historical simulation — not investment advice, just a way to learn.

## Stack

- Python + Streamlit for the app/UI
- `yfinance` for pulling real historical price data
- `pandas` for the return/growth math
- Altair for the charts (so the y-axis actually zooms into price movement instead of flattening everything to zero)
- A live-fetched, cached list of S&P 500 companies (pulled from Wikipedia) powers the "add a stock" dropdown


Then open `http://localhost:8501`.

## Why

Wanted a low-stakes way to poke at real market data and actually see how allocation decisions play out, rather than just trusting a rule of thumb. Still very much a work in progress.
