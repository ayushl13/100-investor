# PortfolioLab

**Want to open the site?**

Already have it cloned? Open the project folder in VS Code, open its built-in terminal (menu bar → Terminal → New Terminal — it opens already inside the right folder, nothing else to do), and paste this:

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

Either way, it'll open automatically in your browser.

A little Streamlit app I built to make sense of investing basics — pick a risk level, punch in an amount, and see how that hypothetical portfolio would've actually done over the last 5 years using real market data.

Started as a way to actually understand what "diversification" and "risk" mean with real numbers instead of just reading about it.

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

## Running it locally

Already have it cloned? Open the project folder in VS Code, open its built-in terminal (menu bar → Terminal → New Terminal — it opens already inside the right folder, nothing else to do), and paste this:

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

Then open `http://localhost:8501`.

## Why

Wanted a low-stakes way to poke at real market data and actually see how allocation decisions play out, rather than just trusting a rule of thumb. Still very much a work in progress.
