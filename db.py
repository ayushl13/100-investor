import streamlit as st
import psycopg2
import yfinance as yf
import pandas as pd
from psycopg2.extras import RealDictCursor, Json
from contextlib import contextmanager
from datetime import datetime, timezone

STARTING_CASH = 100000.00


def get_connection():
    return psycopg2.connect(st.secrets["DATABASE_URL"])


@contextmanager
def db_cursor(commit=False):
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        yield cur
        if commit:
            conn.commit()
    finally:
        conn.close()


# =========================================================
# PLAYERS
# =========================================================

def get_or_create_player(email, display_name):
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT * FROM trading.players WHERE email = %s", (email,))
        player = cur.fetchone()
        if player:
            return player

        cur.execute(
            """
            INSERT INTO trading.players (email, display_name, cash_balance, starting_cash)
            VALUES (%s, %s, %s, %s)
            RETURNING *
            """,
            (email, display_name, STARTING_CASH, STARTING_CASH)
        )
        return cur.fetchone()


def get_player(email):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM trading.players WHERE email = %s", (email,))
        return cur.fetchone()


def get_all_players():
    with db_cursor() as cur:
        cur.execute("SELECT * FROM trading.players ORDER BY email")
        return cur.fetchall()


# =========================================================
# USERS / AUTH
# =========================================================

def create_user(name, email, salt, password_hash):
    email_key = email.strip().lower()
    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO trading.users (email, name, salt, password_hash)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING email
            """,
            (email_key, name.strip(), salt, password_hash)
        )
        if cur.fetchone() is None:
            return False, "An account with this email already exists."
        return True, "Account created."


def get_user_by_email(email):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM trading.users WHERE email = %s", (email.strip().lower(),))
        return cur.fetchone()


def set_session_token(email, token):
    with db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE trading.users SET session_token = %s WHERE email = %s",
            (token, email.strip().lower())
        )


def get_user_by_session_token(token):
    if not token:
        return None
    with db_cursor() as cur:
        cur.execute("SELECT * FROM trading.users WHERE session_token = %s", (token,))
        return cur.fetchone()


def clear_session_token(email):
    if not email:
        return
    with db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE trading.users SET session_token = NULL WHERE email = %s",
            (email.strip().lower(),)
        )


def save_portfolio_settings(email, investment_amount, risk_tolerance, custom_holdings):
    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            UPDATE trading.users
            SET investment_amount = %s, risk_tolerance = %s, custom_holdings = %s
            WHERE email = %s
            """,
            (investment_amount, risk_tolerance, Json(custom_holdings), email.strip().lower())
        )


def get_portfolio_settings(email):
    with db_cursor() as cur:
        cur.execute(
            "SELECT investment_amount, risk_tolerance, custom_holdings FROM trading.users WHERE email = %s",
            (email.strip().lower(),)
        )
        return cur.fetchone()


# =========================================================
# HOLDINGS
# =========================================================

def get_holdings(email):
    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM trading.holdings WHERE player_email = %s ORDER BY ticker",
            (email,)
        )
        return cur.fetchall()


def get_all_holdings():
    with db_cursor() as cur:
        cur.execute("SELECT * FROM trading.holdings")
        return cur.fetchall()


# =========================================================
# TRADES (BUY / SELL)
# =========================================================

def execute_buy(email, ticker, shares, price_per_share):
    if shares <= 0:
        return False, "Enter a positive number of shares."

    total_cost = shares * price_per_share

    with db_cursor(commit=True) as cur:
        cur.execute(
            "SELECT cash_balance FROM trading.players WHERE email = %s FOR UPDATE",
            (email,)
        )
        player = cur.fetchone()

        if player is None:
            return False, "Player not found."

        if float(player["cash_balance"]) < total_cost:
            return False, (
                f"Not enough buying power. You have "
                f"${float(player['cash_balance']):,.2f}, this trade costs "
                f"${total_cost:,.2f}."
            )

        cur.execute(
            "UPDATE trading.players SET cash_balance = cash_balance - %s WHERE email = %s",
            (total_cost, email)
        )

        cur.execute(
            "SELECT shares, avg_cost_basis FROM trading.holdings "
            "WHERE player_email = %s AND ticker = %s FOR UPDATE",
            (email, ticker)
        )
        existing = cur.fetchone()

        if existing:
            new_shares = float(existing["shares"]) + shares
            new_avg_cost = (
                (float(existing["shares"]) * float(existing["avg_cost_basis"])) + total_cost
            ) / new_shares

            cur.execute(
                "UPDATE trading.holdings SET shares = %s, avg_cost_basis = %s "
                "WHERE player_email = %s AND ticker = %s",
                (new_shares, new_avg_cost, email, ticker)
            )
        else:
            cur.execute(
                "INSERT INTO trading.holdings (player_email, ticker, shares, avg_cost_basis) "
                "VALUES (%s, %s, %s, %s)",
                (email, ticker, shares, price_per_share)
            )

        cur.execute(
            """
            INSERT INTO trading.trades
                (player_email, ticker, action, shares, price_per_share, total_amount)
            VALUES (%s, %s, 'BUY', %s, %s, %s)
            """,
            (email, ticker, shares, price_per_share, total_cost)
        )

        return True, f"Bought {shares:.4f} shares of {ticker} for ${total_cost:,.2f}."


def execute_sell(email, ticker, shares, price_per_share):
    if shares <= 0:
        return False, "Enter a positive number of shares."

    proceeds = shares * price_per_share

    with db_cursor(commit=True) as cur:
        cur.execute(
            "SELECT shares FROM trading.holdings "
            "WHERE player_email = %s AND ticker = %s FOR UPDATE",
            (email, ticker)
        )
        existing = cur.fetchone()

        held = float(existing["shares"]) if existing else 0.0

        if held < shares - 1e-9:
            return False, f"You only hold {held:.4f} shares of {ticker}, can't sell {shares:.4f}."

        new_shares = held - shares

        if new_shares <= 1e-6:
            cur.execute(
                "DELETE FROM trading.holdings WHERE player_email = %s AND ticker = %s",
                (email, ticker)
            )
        else:
            cur.execute(
                "UPDATE trading.holdings SET shares = %s WHERE player_email = %s AND ticker = %s",
                (new_shares, email, ticker)
            )

        cur.execute(
            "UPDATE trading.players SET cash_balance = cash_balance + %s WHERE email = %s",
            (proceeds, email)
        )

        cur.execute(
            """
            INSERT INTO trading.trades
                (player_email, ticker, action, shares, price_per_share, total_amount)
            VALUES (%s, %s, 'SELL', %s, %s, %s)
            """,
            (email, ticker, shares, price_per_share, proceeds)
        )

        return True, f"Sold {shares:.4f} shares of {ticker} for ${proceeds:,.2f}."


def get_trade_history(email, limit=50):
    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM trading.trades WHERE player_email = %s "
            "ORDER BY executed_at DESC LIMIT %s",
            (email, limit)
        )
        return cur.fetchall()


def get_all_trades_since(email, since_dt):
    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM trading.trades WHERE player_email = %s AND executed_at >= %s "
            "ORDER BY executed_at ASC",
            (email, since_dt)
        )
        return cur.fetchall()


# =========================================================
# CHALLENGES
# =========================================================

def seed_default_challenges_if_empty():
    with db_cursor(commit=True) as cur:
        cur.execute("SELECT COUNT(*) AS n FROM trading.challenges")
        if cur.fetchone()["n"] > 0:
            return

        cur.execute(
            """
            INSERT INTO trading.challenges
                (title, description, period, starts_at, ends_at, target_return_pct, reward_points, reward_cash)
            VALUES
                ('Daily Trader', 'Make at least one trade today.', 'daily',
                 date_trunc('day', now()), date_trunc('day', now()) + interval '1 day',
                 NULL, 10, 100),
                ('Weekly Beat the Market', 'Reach a 2% portfolio return this week.', 'weekly',
                 date_trunc('week', now()), date_trunc('week', now()) + interval '7 days',
                 2.0, 50, 1000),
                ('Weekly High Roller', 'Reach a 5% portfolio return this week.', 'weekly',
                 date_trunc('week', now()), date_trunc('week', now()) + interval '7 days',
                 5.0, 150, 2500)
            """
        )


def get_active_challenges():
    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM trading.challenges WHERE ends_at > now() ORDER BY starts_at, id"
        )
        return cur.fetchall()


def join_challenge(challenge_id, email, starting_value):
    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            INSERT INTO trading.challenge_participants (challenge_id, player_email, starting_value)
            VALUES (%s, %s, %s)
            ON CONFLICT (challenge_id, player_email) DO NOTHING
            RETURNING *
            """,
            (challenge_id, email, starting_value)
        )
        return cur.fetchone()


def get_my_challenge_participations(email):
    with db_cursor() as cur:
        cur.execute(
            """
            SELECT cp.*, c.title, c.description, c.period, c.starts_at, c.ends_at,
                   c.target_return_pct, c.reward_points, c.reward_cash
            FROM trading.challenge_participants cp
            JOIN trading.challenges c ON c.id = cp.challenge_id
            WHERE cp.player_email = %s
            ORDER BY cp.joined_at DESC
            """,
            (email,)
        )
        return cur.fetchall()


def complete_challenge(participant_id, email, reward_points, reward_cash):
    with db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE trading.challenge_participants SET completed = TRUE, completed_at = now() "
            "WHERE id = %s AND completed = FALSE",
            (participant_id,)
        )
        if cur.rowcount == 0:
            return

        cur.execute(
            "UPDATE trading.players SET total_points = total_points + %s, "
            "cash_balance = cash_balance + %s WHERE email = %s",
            (reward_points, reward_cash, email)
        )


def check_and_complete_challenges(email, current_portfolio_value):
    participations = get_my_challenge_participations(email)
    newly_completed = []

    for p in participations:
        if p["completed"]:
            continue

        target = p["target_return_pct"]

        if target is not None:
            starting_value = float(p["starting_value"])
            current_return_pct = (
                (current_portfolio_value - starting_value) / starting_value * 100
                if starting_value else 0
            )
            if current_return_pct >= float(target):
                complete_challenge(p["id"], email, float(p["reward_points"]), float(p["reward_cash"]))
                newly_completed.append(p["title"])
        else:
            # Participation-style challenge (no target %): complete once the
            # player has made at least one trade since joining it.
            trades_since = get_all_trades_since(email, p["joined_at"])
            if trades_since:
                complete_challenge(p["id"], email, float(p["reward_points"]), float(p["reward_cash"]))
                newly_completed.append(p["title"])

    return newly_completed


# =========================================================
# LEADERBOARD / PORTFOLIO VALUATION
# =========================================================

def fetch_current_prices(tickers):
    prices = {}
    if not tickers:
        return prices

    try:
        data = yf.download(tickers, period="1d", auto_adjust=True, progress=False)
        close = data["Close"]
        if isinstance(close, pd.Series):
            prices[tickers[0]] = float(close.iloc[-1])
        else:
            for t in tickers:
                if t in close.columns:
                    series = close[t].dropna()
                    if not series.empty:
                        prices[t] = float(series.iloc[-1])
    except Exception:
        pass

    return prices


def compute_leaderboard():
    players = get_all_players()
    all_holdings = get_all_holdings()

    tickers = sorted(set(h["ticker"] for h in all_holdings))
    prices = fetch_current_prices(tickers)

    holdings_by_player = {}
    for h in all_holdings:
        holdings_by_player.setdefault(h["player_email"], []).append(h)

    rows = []

    for p in players:
        email = p["email"]
        market_value = 0.0

        for h in holdings_by_player.get(email, []):
            price = prices.get(h["ticker"], float(h["avg_cost_basis"]))
            market_value += float(h["shares"]) * price

        cash = float(p["cash_balance"])
        total_value = cash + market_value
        starting = float(p["starting_cash"])
        return_pct = ((total_value - starting) / starting * 100) if starting else 0.0

        rows.append({
            "email": email,
            "display_name": p["display_name"],
            "cash_balance": cash,
            "market_value": market_value,
            "total_value": total_value,
            "return_pct": return_pct,
            "total_points": float(p["total_points"]),
            "started_at": p["created_at"],
        })

    rows.sort(key=lambda r: r["return_pct"], reverse=True)

    for i, r in enumerate(rows, start=1):
        r["rank"] = i

    return rows


def get_portfolio_value_now(email):
    player = get_player(email)
    if player is None:
        return None

    holdings = get_holdings(email)
    tickers = [h["ticker"] for h in holdings]
    prices = fetch_current_prices(tickers)

    market_value = sum(
        float(h["shares"]) * prices.get(h["ticker"], float(h["avg_cost_basis"]))
        for h in holdings
    )

    return float(player["cash_balance"]) + market_value


def get_portfolio_history(email):
    player = get_player(email)
    if player is None:
        return pd.Series(dtype=float)

    with db_cursor() as cur:
        cur.execute(
            "SELECT * FROM trading.trades WHERE player_email = %s ORDER BY executed_at ASC",
            (email,)
        )
        trades = cur.fetchall()

    start_date = player["created_at"]

    if not trades:
        idx = pd.date_range(start=start_date.date(), end=pd.Timestamp.now().date(), freq="D")
        return pd.Series(float(player["starting_cash"]), index=idx)

    tickers = sorted(set(t["ticker"] for t in trades))

    try:
        price_data = yf.download(
            tickers,
            start=start_date.date(),
            auto_adjust=True,
            progress=False
        )
        close = price_data["Close"]
        if isinstance(close, pd.Series):
            close = close.to_frame(name=tickers[0])
    except Exception:
        close = pd.DataFrame()

    if close.empty:
        idx = pd.date_range(start=start_date.date(), end=pd.Timestamp.now().date(), freq="D")
        return pd.Series(float(player["starting_cash"]), index=idx)

    cash = float(player["starting_cash"])
    shares_held = {t: 0.0 for t in tickers}

    trade_idx = 0
    values = []

    for day in close.index:
        while trade_idx < len(trades) and trades[trade_idx]["executed_at"].date() <= day.date():
            t = trades[trade_idx]
            if t["action"] == "BUY":
                cash -= float(t["total_amount"])
                shares_held[t["ticker"]] += float(t["shares"])
            else:
                cash += float(t["total_amount"])
                shares_held[t["ticker"]] -= float(t["shares"])
            trade_idx += 1

        market_value = 0.0
        for t in tickers:
            if shares_held[t] > 0 and t in close.columns:
                price = close.loc[day, t]
                if pd.notna(price):
                    market_value += shares_held[t] * float(price)

        values.append(cash + market_value)

    return pd.Series(values, index=close.index)
