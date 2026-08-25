import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import altair as alt


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="PortfolioLab",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM STYLING
# =========================================================

KINETIC_GRID_JS = r"""
<style>
html, body {
    background: #161618 !important;
    margin: 0;
    overflow: hidden;
}
</style>
<canvas id="kinetic-grid-canvas-local"></canvas>
<script>
(function () {
    var CELL_SIZE = 55;
    var INFLUENCE_RADIUS = 320;
    var MAX_WARP = 22;
    var DOT_SPACING = 28;
    var LERP_SPEED = 0.12;
    var LINE_BASE = { r: 255, g: 255, b: 255, a: 0.13 };
    var NODE_BASE_RADIUS = 1.8;
    var NODE_ACTIVE_RADIUS = 3.2;

    var theme = {
        bg: '#161618',
        lineActive: { r: 74, g: 158, b: 255, a: 0.9 },
        nodeActive: { r: 74, g: 158, b: 255, a: 1.0 },
        glow: '74,158,255',
        ripple: '100,180,255'
    };

    function lerpN(a, b, t) { return a + (b - a) * t; }
    function lerpColor(base, active, t) {
        var r = Math.round(lerpN(base.r, active.r, t));
        var g = Math.round(lerpN(base.g, active.g, t));
        var b = Math.round(lerpN(base.b, active.b, t));
        var a = lerpN(base.a, active.a, t);
        return 'rgba(' + r + ',' + g + ',' + b + ',' + a.toFixed(3) + ')';
    }

    // ---- Try to reach the real top-level page for genuine cursor tracking.
    // Falls back to a self-contained ambient animation if the browser blocks it.
    var win = null, doc = null, canvas = null, REAL_CURSOR = false;

    try {
        var testWin = window.parent;
        var testDoc = testWin.document;
        var probe = testDoc.body.nodeName;  // throws if cross-origin blocked

        if (!testWin.__kineticGridInjected) {
            testWin.__kineticGridInjected = true;
            win = testWin;
            doc = testDoc;

            canvas = doc.createElement('canvas');
            canvas.id = 'kinetic-grid-canvas';
            canvas.style.position = 'fixed';
            canvas.style.top = '0';
            canvas.style.left = '0';
            canvas.style.width = '100vw';
            canvas.style.height = '100vh';
            canvas.style.zIndex = '0';
            canvas.style.pointerEvents = 'none';
            doc.body.insertBefore(canvas, doc.body.firstChild);

            REAL_CURSOR = true;
        }
    } catch (err) {
        REAL_CURSOR = false;
    }

    if (!REAL_CURSOR) {
        win = window;
        doc = document;
        canvas = doc.getElementById('kinetic-grid-canvas-local');
    }

    if (!canvas) { return; }
    var ctx = canvas.getContext('2d');

    var mouse = { x: -9999, y: -9999 };
    var targetMouse = { x: -9999, y: -9999 };
    var ripples = [];
    var size = { w: 0, h: 0 };
    var startTime = performance.now();
    var nextAutoRipple = 2000;

    function setSize() {
        size.w = win.innerWidth;
        size.h = win.innerHeight;
        canvas.width = size.w;
        canvas.height = size.h;
    }
    setSize();
    win.addEventListener('resize', setSize);

    if (REAL_CURSOR) {
        win.addEventListener('mousemove', function (e) {
            targetMouse.x = e.clientX;
            targetMouse.y = e.clientY;
        });
        win.addEventListener('click', function (e) {
            ripples.push({ x: e.clientX, y: e.clientY, radius: 0, opacity: 1, born: performance.now() });
        });
    }

    function getWarpedPoint(gx, gy, col, row, cols, rows) {
        var edgeMargin = 1.5;
        var colPin = Math.min(col / edgeMargin, (cols - 1 - col) / edgeMargin, 1);
        var rowPin = Math.min(row / edgeMargin, (rows - 1 - row) / edgeMargin, 1);
        var pinFactor = colPin * colPin * rowPin * rowPin;

        var dx = gx - mouse.x;
        var dy = gy - mouse.y;
        var dist = Math.sqrt(dx * dx + dy * dy);
        var proximity = Math.max(0, 1 - dist / INFLUENCE_RADIUS) * pinFactor;

        var rx = 0, ry = 0;
        for (var i = 0; i < ripples.length; i++) {
            var r = ripples[i];
            var rdx = gx - r.x;
            var rdy = gy - r.y;
            var rdist = Math.sqrt(rdx * rdx + rdy * rdy);
            var waveWidth = 55;
            var diff = rdist - r.radius;
            if (Math.abs(diff) < waveWidth) {
                var strength = (1 - Math.abs(diff) / waveWidth) * r.opacity * 18 * pinFactor;
                var angle = Math.atan2(rdy, rdx);
                var sign = diff < 0 ? -1 : 1;
                rx += Math.cos(angle) * strength * sign * -1;
                ry += Math.sin(angle) * strength * sign * -1;
            }
        }

        if (dist < INFLUENCE_RADIUS && dist > 0 && pinFactor > 0) {
            var t = dist / INFLUENCE_RADIUS;
            var eased = t < 0.01 ? 0 : (1 - t) * (1 - t) * Math.min(1, dist / 60);
            var warpAmt = eased * MAX_WARP * pinFactor;
            var angle2 = Math.atan2(dy, dx);
            return {
                pt: { x: gx - Math.cos(angle2) * warpAmt + rx, y: gy - Math.sin(angle2) * warpAmt + ry },
                proximity: proximity
            };
        }
        return { pt: { x: gx + rx, y: gy + ry }, proximity: proximity };
    }

    function draw(now) {
        var W = size.w, H = size.h;
        ctx.clearRect(0, 0, W, H);
        ctx.fillStyle = theme.bg;
        ctx.fillRect(0, 0, W, H);

        ctx.fillStyle = 'rgba(255,255,255,0.05)';
        for (var x = DOT_SPACING / 2; x < W; x += DOT_SPACING) {
            for (var y = DOT_SPACING / 2; y < H; y += DOT_SPACING) {
                ctx.beginPath();
                ctx.arc(x, y, 0.7, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        if (REAL_CURSOR) {
            mouse.x = lerpN(mouse.x, targetMouse.x, LERP_SPEED);
            mouse.y = lerpN(mouse.y, targetMouse.y, LERP_SPEED);
        } else {
            var elapsed = (now - startTime) / 1000;
            mouse.x = W / 2 + Math.sin(elapsed * 0.25) * (W * 0.35);
            mouse.y = H / 2 + Math.sin(elapsed * 0.4) * (H * 0.3);

            if (now > nextAutoRipple) {
                ripples.push({ x: mouse.x, y: mouse.y, radius: 0, opacity: 1, born: now });
                nextAutoRipple = now + 3200 + Math.random() * 1800;
            }
        }

        for (var i = ripples.length - 1; i >= 0; i--) {
            var r = ripples[i];
            var age = (now - r.born) / 1000;
            r.radius = Math.max(0, age * 400);
            r.opacity = Math.max(0, 1 - age * 1.2);
            if (r.opacity <= 0) ripples.splice(i, 1);
        }

        var cols = Math.max(2, Math.ceil(W / CELL_SIZE)) + 1;
        var rows = Math.max(2, Math.ceil(H / CELL_SIZE)) + 1;
        var cellW = W / (cols - 1);
        var cellH = H / (rows - 1);

        var pts = [];
        var prox = [];
        for (var row = 0; row < rows; row++) {
            pts[row] = [];
            prox[row] = [];
            for (var col = 0; col < cols; col++) {
                var res = getWarpedPoint(col * cellW, row * cellH, col, row, cols, rows);
                pts[row][col] = res.pt;
                prox[row][col] = res.proximity;
            }
        }

        function drawSeg(p1, p2, pr1, pr2) {
            var avg = (pr1 + pr2) / 2;
            var t = avg * avg * (3 - 2 * avg);
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = lerpColor(LINE_BASE, theme.lineActive, t);
            ctx.lineWidth = lerpN(0.8, 1.5, t);
            ctx.stroke();
        }

        ctx.lineCap = 'butt';
        for (var row = 0; row < rows; row++)
            for (var col = 0; col < cols - 1; col++)
                drawSeg(pts[row][col], pts[row][col + 1], prox[row][col], prox[row][col + 1]);
        for (var col = 0; col < cols; col++)
            for (var row = 0; row < rows - 1; row++)
                drawSeg(pts[row][col], pts[row + 1][col], prox[row][col], prox[row + 1][col]);

        for (var row = 0; row < rows; row++) {
            for (var col = 0; col < cols; col++) {
                var p = pts[row][col];
                var pr = prox[row][col];
                var t = pr * pr * (3 - 2 * pr);
                var rad = lerpN(NODE_BASE_RADIUS, NODE_ACTIVE_RADIUS, t);

                if (t > 0.3) {
                    var glowR = rad + lerpN(0, 6, (t - 0.3) / 0.7);
                    var grd = ctx.createRadialGradient(p.x, p.y, rad * 0.5, p.x, p.y, glowR);
                    grd.addColorStop(0, 'rgba(' + theme.glow + ',' + (t * 0.3).toFixed(3) + ')');
                    grd.addColorStop(1, 'rgba(' + theme.glow + ',0)');
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, glowR, 0, Math.PI * 2);
                    ctx.fillStyle = grd;
                    ctx.fill();
                }

                ctx.beginPath();
                ctx.arc(p.x, p.y, rad, 0, Math.PI * 2);
                ctx.fillStyle = lerpColor({ r: 255, g: 255, b: 255, a: 0.2 }, theme.nodeActive, t);
                ctx.fill();
            }
        }

        for (var i2 = 0; i2 < ripples.length; i2++) {
            var rp = ripples[i2];
            var safeRadius = Math.max(0, rp.radius);
            ctx.beginPath();
            ctx.arc(rp.x, rp.y, safeRadius, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(' + theme.ripple + ',' + (rp.opacity * 0.28).toFixed(3) + ')';
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }
    }

    function animate(now) {
        draw(now);
        win.requestAnimationFrame(animate);
    }
    win.requestAnimationFrame(animate);
})();
</script>
"""


BACKGROUND_CSS = """
<style>
iframe {
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
    z-index: -1 !important;
    pointer-events: none !important;
    border: none !important;
}
html, body {
    background: #161618 !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stMain"],
.stApp {
    background: transparent !important;
}
[data-testid="stSidebar"] {
    background-color: rgba(30, 30, 34, 0.9) !important;
}
</style>
"""

def render_kinetic_grid_background():
    st.markdown(BACKGROUND_CSS, unsafe_allow_html=True)
    components.html(KINETIC_GRID_JS, height=0)

render_kinetic_grid_background()



# =========================================================
# PORTFOLIO DEFINITIONS
# =========================================================

portfolios = {

    "Conservative": {
        "VOO": 0.40,
        "BND": 0.40,
        "VXUS": 0.20
    },

    "Moderate": {
        "VOO": 0.50,
        "QQQ": 0.20,
        "VXUS": 0.20,
        "BND": 0.10
    },

    "Aggressive": {
        "VOO": 0.40,
        "QQQ": 0.30,
        "VXUS": 0.20,
        "BND": 0.10
    }
}


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📊 PortfolioLab")

st.sidebar.caption(
    "Simple portfolio analytics for first-time investors."
)

st.sidebar.divider()

st.sidebar.subheader("Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "🏠 Overview",
        "💼 Portfolio",
        "📈 Performance",
        "⚠️ Risk",
        "🔍 ETF Research",
        "🧪 Scenario Lab",
        "ℹ️ About"
    ],
    label_visibility="collapsed"
)

st.sidebar.divider()

st.sidebar.subheader("Portfolio Settings")

amount = st.sidebar.number_input(
    "Investment amount",
    min_value=10.0,
    value=100.0,
    step=10.0
)

risk = st.sidebar.selectbox(
    "Risk tolerance",
    [
        "Conservative",
        "Moderate",
        "Aggressive"
    ]
)

st.sidebar.divider()

st.sidebar.caption(
    "Adjust your investment amount and risk tolerance "
    "to explore different hypothetical portfolios."
)


# =========================================================
# SELECT PORTFOLIO
# =========================================================

portfolio = portfolios[risk]


# =========================================================
# DOWNLOAD HISTORICAL DATA
# =========================================================

prices = yf.download(
    list(portfolio.keys()),
    period="5y",
    auto_adjust=True,
    progress=False
)


# =========================================================
# CLEAN PRICE DATA
# =========================================================

returns = prices["Close"].pct_change().dropna()


# =========================================================
# PORTFOLIO RETURN CALCULATION
# =========================================================

portfolio_returns = pd.Series(
    0.0,
    index=returns.index
)

for ticker, weight in portfolio.items():

    portfolio_returns += (
        returns[ticker] * weight
    )


# =========================================================
# PORTFOLIO GROWTH
# =========================================================

portfolio_growth = (
    1 + portfolio_returns
).cumprod()


final_value = (
    amount * portfolio_growth.iloc[-1]
)


total_return = (
    portfolio_growth.iloc[-1] - 1
)


# =========================================================
# S&P 500 BENCHMARK
# =========================================================

benchmark_returns = returns["VOO"]

benchmark_growth = (
    1 + benchmark_returns
).cumprod()


benchmark_value = (
    amount * benchmark_growth.iloc[-1]
)


benchmark_return = (
    benchmark_growth.iloc[-1] - 1
)


# =========================================================
# RISK CALCULATIONS
# =========================================================

annualized_volatility = (
    portfolio_returns.std()
    * (252 ** 0.5)
)


risk_score = min(
    10,
    max(
        1,
        annualized_volatility * 20
    )
)


# =========================================================
# MAXIMUM DRAWDOWN
# =========================================================

running_peak = (
    portfolio_growth.cummax()
)

drawdown = (
    portfolio_growth / running_peak
) - 1


maximum_drawdown = drawdown.min()


# =========================================================
# ETF INFORMATION
# =========================================================

etf_information = {

    "VOO": {
        "name": "Vanguard S&P 500 ETF",
        "asset_class": "U.S. Equities",
        "focus": "Large-cap U.S. companies",
        "role": "Core equity exposure",
        "description": (
            "Tracks the S&P 500, giving broad exposure to 500 of the largest "
            "U.S. companies across nearly every sector. It's often used as a "
            "core holding because of its low cost and broad diversification."
        )
    },

    "QQQ": {
        "name": "Invesco QQQ",
        "asset_class": "U.S. Equities",
        "focus": "Nasdaq-100 companies",
        "role": "Growth and technology exposure",
        "description": (
            "Tracks the Nasdaq-100, which is heavily weighted toward "
            "technology and other growth-oriented companies. It has "
            "historically offered higher growth potential alongside "
            "higher volatility than the broader market."
        )
    },

    "VXUS": {
        "name": "Vanguard Total International Stock ETF",
        "asset_class": "International Equities",
        "focus": "Companies outside the United States",
        "role": "International diversification",
        "description": (
            "Provides exposure to thousands of companies across developed "
            "and emerging markets outside the U.S., helping diversify a "
            "portfolio away from U.S.-only risk."
        )
    },

    "BND": {
        "name": "Vanguard Total Bond Market ETF",
        "asset_class": "Fixed Income",
        "focus": "U.S. investment-grade bonds",
        "role": "Income and portfolio stability",
        "description": (
            "Holds a broad mix of U.S. investment-grade bonds, providing "
            "steady income and helping cushion a portfolio during stock "
            "market downturns."
        )
    }
}


# =========================================================
# TICKER DETAIL POPUP
# =========================================================

TICKER_RANGES = [
    ("Day", "1d", "5m"),
    ("Week", "5d", "30m"),
    ("Month", "1mo", "1d"),
    ("Year", "1y", "1d"),
    ("YTD", "ytd", "1d"),
]


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ticker_history(ticker, period, interval):
    return yf.Ticker(ticker).history(period=period, interval=interval)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_ticker_fast_info(ticker):
    info = yf.Ticker(ticker).fast_info
    return {
        "last_price": info.get("lastPrice"),
        "previous_close": info.get("previousClose"),
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "year_high": info.get("yearHigh"),
        "year_low": info.get("yearLow"),
        "market_cap": info.get("marketCap"),
        "volume": info.get("lastVolume"),
    }


@st.dialog("Stock Detail", width="large")
def ticker_dialog(ticker):

    name = etf_information.get(ticker, {}).get("name", ticker)
    st.subheader(f"{ticker} — {name}")

    try:
        stats = fetch_ticker_fast_info(ticker)
    except Exception:
        stats = None

    if stats and stats.get("last_price") is not None:
        last_price = stats["last_price"]
        prev_close = stats.get("previous_close")

        stat1, stat2, stat3, stat4 = st.columns(4)

        with stat1:
            if prev_close:
                change = last_price - prev_close
                change_pct = (change / prev_close) * 100
                st.metric(
                    "Price",
                    f"${last_price:,.2f}",
                    f"{change:+.2f} ({change_pct:+.2f}%)"
                )
            else:
                st.metric("Price", f"${last_price:,.2f}")

        with stat2:
            if stats.get("day_high") and stats.get("day_low"):
                st.metric("Day Range", f"${stats['day_low']:,.2f} – ${stats['day_high']:,.2f}")

        with stat3:
            if stats.get("year_high") and stats.get("year_low"):
                st.metric("52-Week Range", f"${stats['year_low']:,.2f} – ${stats['year_high']:,.2f}")

        with stat4:
            if stats.get("market_cap"):
                st.metric("Market Cap", f"${stats['market_cap'] / 1e9:,.1f}B")
            elif stats.get("volume"):
                st.metric("Volume", f"{stats['volume']:,.0f}")

        st.divider()
    else:
        st.warning("Live stats are temporarily unavailable for this ticker.")

    tabs = st.tabs([label for label, _, _ in TICKER_RANGES])

    for tab, (label, period, interval) in zip(tabs, TICKER_RANGES):
        with tab:
            try:
                hist = fetch_ticker_history(ticker, period, interval)
            except Exception:
                hist = None

            if hist is None or hist.empty:
                st.info("No price data available for this range (market may be closed).")
                continue

            line_chart_single(hist["Close"], height=300, y_title="Price ($)")

            range_return = (hist["Close"].iloc[-1] / hist["Close"].iloc[0] - 1) * 100
            st.caption(f"{label} change: {range_return:+.2f}%")

    if ticker in etf_information:
        st.divider()
        st.caption(etf_information[ticker]["focus"])


def ticker_button(ticker, key_suffix, label=None):
    if st.button(label or ticker, key=f"tkr_{ticker}_{key_suffix}", type="tertiary"):
        ticker_dialog(ticker)


def line_chart_single(series, height=350, y_title="Value ($)"):
    df = pd.DataFrame({"Date": series.index, "Value": series.values})
    chart = (
        alt.Chart(df)
        .mark_line(color="#4A9EFF", strokeWidth=2)
        .encode(
            x=alt.X("Date:T", title=None),
            y=alt.Y("Value:Q", title=y_title, scale=alt.Scale(zero=False)),
            tooltip=[alt.Tooltip("Date:T", title="Date"), alt.Tooltip("Value:Q", title="Value", format=",.2f")]
        )
        .properties(height=height)
    )
    st.altair_chart(chart, use_container_width=True)


def line_chart_multi(df, height=400, y_title="Value ($)"):
    frames = [
        pd.DataFrame({"Date": df.index, "Series": col, "Value": df[col].values})
        for col in df.columns
    ]
    long_df = pd.concat(frames, ignore_index=True)
    chart = (
        alt.Chart(long_df)
        .mark_line(strokeWidth=2)
        .encode(
            x=alt.X("Date:T", title=None),
            y=alt.Y("Value:Q", title=y_title, scale=alt.Scale(zero=False)),
            color=alt.Color("Series:N", title=None),
            tooltip=["Date:T", "Series:N", alt.Tooltip("Value:Q", title="Value", format=",.2f")]
        )
        .properties(height=height)
    )
    st.altair_chart(chart, use_container_width=True)


# =========================================================
# OVERVIEW PAGE
# =========================================================

if page == "🏠 Overview":

    st.caption("PERSONAL PORTFOLIO ANALYTICS")

    st.title("Build. Analyze. Understand.")

    st.write(
        "A simple portfolio research tool that helps "
        "first-time investors explore allocation, "
        "performance, and risk."
    )

    st.divider()

    # ---------------------------------------------
    # PORTFOLIO SUMMARY
    # ---------------------------------------------

    st.subheader(
        f"{risk} Portfolio"
    )

    st.caption(
        "Five-year historical analysis"
    )

    overview1, overview2, overview3, overview4 = st.columns(4)

    with overview1:

        st.metric(
            "Investment",
            f"${amount:,.2f}"
        )

    with overview2:

        st.metric(
            "Historical Value",
            f"${final_value:,.2f}",
            f"{total_return * 100:+.2f}%"
        )

    with overview3:

        st.metric(
            "S&P 500 Value",
            f"${benchmark_value:,.2f}"
        )

    with overview4:

        st.metric(
            "Risk Score",
            f"{risk_score:.1f}/10"
        )

    st.divider()

    # ---------------------------------------------
    # GROWTH CHART
    # ---------------------------------------------

    st.subheader(
        "How Your Investment Could Have Grown"
    )

    overview_chart = pd.DataFrame(
        {
            "Your Portfolio":
                portfolio_growth * amount,

            "S&P 500":
                benchmark_growth * amount
        }
    )

    line_chart_multi(overview_chart, height=400)

    st.caption(
        "Historical simulation based on the selected "
        "portfolio allocation. This is not a prediction."
    )

    st.divider()

    # ---------------------------------------------
    # PORTFOLIO SNAPSHOT
    # ---------------------------------------------

    st.subheader(
        "Portfolio Snapshot"
    )

    snapshot_col1, snapshot_col2 = st.columns(2)

    with snapshot_col1:

        st.write("**Allocation**")

        for ticker, weight in portfolio.items():

            alloc_col1, alloc_col2 = st.columns([1, 2])

            with alloc_col1:
                ticker_button(ticker, key_suffix="overview")

            with alloc_col2:
                st.write(f"{weight * 100:.0f}%")

    with snapshot_col2:

        st.write("**Risk Profile**")

        if risk == "Conservative":

            st.write(
                "Lower-risk allocation with a larger "
                "bond position."
            )

        elif risk == "Moderate":

            st.write(
                "Balanced exposure across U.S. equities, "
                "international equities, growth stocks, "
                "and bonds."
            )

        else:

            st.write(
                "Higher equity exposure designed for "
                "greater long-term growth potential "
                "with increased volatility."
            )


# =========================================================
# PORTFOLIO PAGE
# =========================================================

elif page == "💼 Portfolio":

    st.caption("PORTFOLIO CONSTRUCTION")

    st.title("Your Portfolio")

    st.write(
        f"Your **{risk.lower()}** portfolio distributes "
        f"${amount:,.2f} across {len(portfolio)} ETFs."
    )

    st.divider()

    # ---------------------------------------------
    # HOLDINGS
    # ---------------------------------------------

    st.subheader("Holdings")

    allocation_data = pd.DataFrame(
        {
            "ETF": list(portfolio.keys()),

            "Allocation": [
                weight * 100
                for weight in portfolio.values()
            ],

            "Investment": [
                amount * weight
                for weight in portfolio.values()
            ]
        }
    )

    allocation_display = allocation_data.copy()

    allocation_display["Allocation"] = (
        allocation_display["Allocation"]
        .map(lambda x: f"{x:.0f}%")
    )

    allocation_display["Investment"] = (
        allocation_display["Investment"]
        .map(lambda x: f"${x:,.2f}")
    )

    st.dataframe(
        allocation_display,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # ---------------------------------------------
    # PORTFOLIO VALUE
    # ---------------------------------------------

    st.subheader("Portfolio Value")

    line_chart_single(portfolio_growth * amount, height=350)

    st.caption(
        "Historical value of this portfolio over the trailing five years."
    )

    st.divider()

    # ---------------------------------------------
    # ALLOCATION CHART
    # ---------------------------------------------

    st.subheader("Allocation Breakdown")

    chart_data = pd.DataFrame(
        {
            "Allocation": [
                weight * 100
                for weight in portfolio.values()
            ]
        },
        index=portfolio.keys()
    )

    st.bar_chart(
        chart_data,
        height=350
    )

    st.divider()

    # ---------------------------------------------
    # ETF DESCRIPTIONS
    # ---------------------------------------------

    st.subheader("What You Own")

    for ticker in portfolio.keys():

        info = etf_information[ticker]

        ticker_button(ticker, key_suffix="whatyouown", label=f"**{ticker}**")

        st.markdown(
            f"<div style='font-size:1.05rem; line-height:1.55; color:#FAFAFA; "
            f"margin-bottom:0.6rem;'>"
            f"<strong>{info['name']}</strong> — {info['description']}"
            f"</div>",
            unsafe_allow_html=True
        )

        st.markdown(
            f"<div style='font-size:0.85rem; color:#8FBFFF; margin-top:0.4rem;'>"
            f"{info['role']} · {info['focus']}"
            f"</div>",
            unsafe_allow_html=True
        )

        st.divider()


# =========================================================
# PERFORMANCE PAGE
# =========================================================

elif page == "📈 Performance":

    st.caption("HISTORICAL PERFORMANCE")

    st.title("Performance")

    st.write(
        "See how your hypothetical portfolio would have "
        "performed over the past five years compared "
        "with the S&P 500."
    )

    st.divider()

    # ---------------------------------------------
    # PERFORMANCE METRICS
    # ---------------------------------------------

    portfolio_return_pct = (
        total_return * 100
    )

    benchmark_return_pct = (
        benchmark_return * 100
    )

    relative_performance = (
        portfolio_return_pct
        - benchmark_return_pct
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Portfolio Return",
            f"{portfolio_return_pct:+.2f}%"
        )

    with col2:

        st.metric(
            "S&P 500 Return",
            f"{benchmark_return_pct:+.2f}%"
        )

    with col3:

        st.metric(
            "Difference vs. S&P 500",
            f"{relative_performance:+.2f}%"
        )

    st.divider()

    # ---------------------------------------------
    # PORTFOLIO GROWTH
    # ---------------------------------------------

    st.subheader("Portfolio Growth")

    portfolio_value = (
        portfolio_growth * amount
    )

    line_chart_single(portfolio_value, height=400)

    st.caption(
        "Historical value of the hypothetical portfolio "
        "assuming the original allocation remained constant."
    )

    st.divider()

    # ---------------------------------------------
    # BENCHMARK COMPARISON
    # ---------------------------------------------

    st.subheader("Portfolio vs. S&P 500")

    comparison = pd.DataFrame(
        {
            "Your Portfolio":
                portfolio_growth * amount,

            "S&P 500":
                benchmark_growth * amount
        }
    )

    line_chart_multi(comparison, height=400)

    st.divider()

    # ---------------------------------------------
    # DAILY PERFORMANCE
    # ---------------------------------------------

    st.subheader("Daily Performance")

    best_day = (
        portfolio_returns.max() * 100
    )

    worst_day = (
        portfolio_returns.min() * 100
    )

    day_col1, day_col2 = st.columns(2)

    with day_col1:

        st.metric(
            "Best Day",
            f"{best_day:+.2f}%"
        )

    with day_col2:

        st.metric(
            "Worst Day",
            f"{worst_day:+.2f}%"
        )


# =========================================================
# RISK PAGE
# =========================================================

elif page == "⚠️ Risk":

    st.caption("PORTFOLIO RISK ANALYSIS")

    st.title("Understand Your Risk")

    st.write(
        "Evaluate the historical volatility and downside "
        "risk associated with your portfolio."
    )

    st.divider()

    # ---------------------------------------------
    # RISK METRICS
    # ---------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Risk Score",
            f"{risk_score:.1f} / 10"
        )

    with col2:

        st.metric(
            "Annualized Volatility",
            f"{annualized_volatility * 100:.2f}%"
        )

    with col3:

        st.metric(
            "Maximum Drawdown",
            f"{maximum_drawdown * 100:.2f}%"
        )

    st.divider()

    # ---------------------------------------------
    # DRAWDOWN CHART
    # ---------------------------------------------

    st.subheader("Historical Drawdown")

    drawdown_chart = (
        drawdown * 100
    )

    st.area_chart(
        drawdown_chart,
        height=350
    )

    st.caption(
        "Drawdown measures the decline from a previous "
        "portfolio peak."
    )

    st.divider()

    # ---------------------------------------------
    # RISK INTERPRETATION
    # ---------------------------------------------

    st.subheader("Risk Interpretation")

    if risk_score < 4:

        st.success(
            "This portfolio has historically experienced "
            "relatively low volatility."
        )

    elif risk_score < 7:

        st.info(
            "This portfolio has historically experienced "
            "moderate volatility."
        )

    else:

        st.warning(
            "This portfolio has historically experienced "
            "relatively high volatility."
        )

    st.write(
        f"**Annualized volatility:** "
        f"{annualized_volatility * 100:.2f}%"
    )

    st.write(
        f"**Maximum historical drawdown:** "
        f"{maximum_drawdown * 100:.2f}%"
    )

    st.caption(
        "The risk score is a simplified educational measure "
        "based on historical portfolio volatility. It is not "
        "an official investment risk rating."
    )


# =========================================================
# ETF RESEARCH PAGE
# =========================================================

elif page == "🔍 ETF Research":

    st.caption("ETF RESEARCH")

    st.title("Explore Your ETFs")

    st.write(
        "Learn what each ETF in your portfolio is designed "
        "to provide exposure to."
    )

    st.divider()

    # ---------------------------------------------
    # ETF SELECTOR
    # ---------------------------------------------

    selected_etf = st.selectbox(
        "Select an ETF",
        list(etf_information.keys())
    )

    info = etf_information[selected_etf]

    st.subheader(
        f"{selected_etf} — {info['name']}"
    )

    ticker_button(selected_etf, key_suffix="etfresearch", label="View Chart & Stats")

    # ---------------------------------------------
    # ETF DETAILS
    # ---------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Asset Class",
            info["asset_class"]
        )

    with col2:

        st.metric(
            "Investment Focus",
            info["focus"]
        )

    with col3:

        st.metric(
            "Portfolio Role",
            info["role"]
        )

    st.divider()

    # ---------------------------------------------
    # HISTORICAL DATA
    # ---------------------------------------------

    st.subheader("Historical Performance")

    etf_prices = yf.download(
        selected_etf,
        period="5y",
        auto_adjust=True,
        progress=False
    )

    etf_close = etf_prices["Close"]

    etf_returns = (
        etf_close
        .pct_change()
        .dropna()
    )

    etf_growth = (
        1 + etf_returns
    ).cumprod()

    etf_return = (
        etf_growth.iloc[-1] - 1
    )

    current_price = (
        etf_close.iloc[-1]
    )

    metric1, metric2 = st.columns(2)

    with metric1:

        st.metric(
            "Current Price",
            f"${float(current_price):,.2f}"
        )

    with metric2:

        st.metric(
            "5-Year Return",
            f"{float(etf_return) * 100:+.2f}%"
        )

    st.subheader("Historical Price")

    line_chart_single(etf_close, height=400, y_title="Price ($)")

    # ---------------------------------------------
    # USER EXPOSURE
    # ---------------------------------------------

    if selected_etf in portfolio:

        weight = portfolio[selected_etf]

        investment = (
            amount * weight
        )

        st.divider()

        st.subheader("Your Exposure")

        exposure_col1, exposure_col2 = st.columns(2)

        with exposure_col1:

            st.metric(
                "Portfolio Allocation",
                f"{weight * 100:.0f}%"
            )

        with exposure_col2:

            st.metric(
                "Your Investment",
                f"${investment:,.2f}"
            )

        st.info(
            f"{selected_etf} represents "
            f"{weight * 100:.0f}% of your current "
            f"hypothetical portfolio."
        )


# =========================================================
# SCENARIO LAB PAGE
# =========================================================

elif page == "🧪 Scenario Lab":

    st.caption("WHAT-IF ANALYSIS")

    st.title("Scenario Lab")

    st.write(
        "Change the investment amount and risk profile "
        "to explore how different hypothetical portfolios "
        "would have performed historically."
    )

    st.divider()

    # ---------------------------------------------
    # SCENARIO INPUTS
    # ---------------------------------------------

    st.subheader("Build Your Scenario")

    scenario_col1, scenario_col2 = st.columns(2)

    with scenario_col1:

        scenario_amount = st.number_input(
            "Starting investment",
            min_value=10.0,
            value=100.0,
            step=50.0,
            key="scenario_amount"
        )

    with scenario_col2:

        scenario_risk = st.selectbox(
            "Risk profile",
            [
                "Conservative",
                "Moderate",
                "Aggressive"
            ],
            key="scenario_risk"
        )

    scenario_portfolio = portfolios[
        scenario_risk
    ]

    st.divider()

    # ---------------------------------------------
    # SCENARIO DATA
    # ---------------------------------------------

    scenario_prices = yf.download(
        list(scenario_portfolio.keys()),
        period="5y",
        auto_adjust=True,
        progress=False
    )

    scenario_returns = (
        scenario_prices["Close"]
        .pct_change()
        .dropna()
    )

    scenario_portfolio_returns = pd.Series(
        0.0,
        index=scenario_returns.index
    )

    for ticker, weight in scenario_portfolio.items():

        scenario_portfolio_returns += (
            scenario_returns[ticker]
            * weight
        )

    scenario_growth = (
        1 + scenario_portfolio_returns
    ).cumprod()

    scenario_final_value = (
        scenario_amount
        * scenario_growth.iloc[-1]
    )

    scenario_total_return = (
        scenario_growth.iloc[-1] - 1
    )

    # ---------------------------------------------
    # SCENARIO RESULTS
    # ---------------------------------------------

    st.subheader("Scenario Results")

    result1, result2, result3 = st.columns(3)

    with result1:

        st.metric(
            "Starting Investment",
            f"${scenario_amount:,.2f}"
        )

    with result2:

        st.metric(
            "Historical Ending Value",
            f"${scenario_final_value:,.2f}"
        )

    with result3:

        st.metric(
            "Historical Return",
            f"{scenario_total_return * 100:+.2f}%"
        )

    st.divider()

    # ---------------------------------------------
    # SCENARIO GROWTH
    # ---------------------------------------------

    st.subheader("Historical Scenario Growth")

    scenario_value = (
        scenario_growth
        * scenario_amount
    )

    line_chart_single(scenario_value, height=400)

    st.divider()

    # ---------------------------------------------
    # SCENARIO ALLOCATION
    # ---------------------------------------------

    st.subheader(
        f"{scenario_risk} Allocation"
    )

    scenario_allocation = pd.DataFrame(
        {
            "ETF": list(
                scenario_portfolio.keys()
            ),

            "Allocation": [
                weight * 100
                for weight
                in scenario_portfolio.values()
            ],

            "Investment": [
                scenario_amount * weight
                for weight
                in scenario_portfolio.values()
            ]
        }
    )

    scenario_display = (
        scenario_allocation.copy()
    )

    scenario_display["Allocation"] = (
        scenario_display["Allocation"]
        .map(lambda x: f"{x:.0f}%")
    )

    scenario_display["Investment"] = (
        scenario_display["Investment"]
        .map(lambda x: f"${x:,.2f}")
    )

    st.dataframe(
        scenario_display,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.info(
        "Scenario results are based on historical market "
        "data and are intended for educational purposes only. "
        "Past performance does not guarantee future results."
    )

# =========================================================
# ABOUT PAGE
# =========================================================

elif page == "ℹ️ About":

    st.caption("ABOUT PORTFOLIOLAB")

    st.title("Making Investing Easier to Understand.")

    st.write(
        "PortfolioLab is an educational portfolio analytics "
        "tool designed to help students and first-time investors "
        "understand how different investment decisions can affect "
        "portfolio performance and risk."
    )

    st.divider()

    # -----------------------------------------------------
    # WHY I BUILT THIS
    # -----------------------------------------------------

    st.subheader("Why I Built This")

    st.write(
        "Investing can feel intimidating when you're first "
        "getting started. There are thousands of securities, "
        "different asset classes, and countless opinions about "
        "what investors should buy."
    )

    st.write(
        "I built PortfolioLab as a simple way to explore those "
        "decisions using real market data without requiring "
        "advanced financial modeling knowledge."
    )

    st.write(
        "The goal is not to tell users what to invest in. "
        "Instead, it is designed to help users understand "
        "the relationship between allocation, historical "
        "performance, diversification, and risk."
    )

    st.divider()

    # -----------------------------------------------------
    # WHAT YOU CAN DO
    # -----------------------------------------------------

    st.subheader("What You Can Explore")

    about_col1, about_col2 = st.columns(2)

    with about_col1:

        st.markdown("### 💼 Build a Portfolio")

        st.write(
            "Explore Conservative, Moderate, and Aggressive "
            "portfolio allocations using a small group of "
            "diversified ETFs."
        )

        st.markdown("### 📈 Analyze Performance")

        st.write(
            "Compare hypothetical portfolio performance "
            "with the S&P 500 over historical periods."
        )

        st.markdown("### 🔍 Research ETFs")

        st.write(
            "Learn what individual ETFs are designed to "
            "provide exposure to and how they have performed "
            "historically."
        )

    with about_col2:

        st.markdown("### ⚠️ Understand Risk")

        st.write(
            "Explore volatility, maximum drawdown, and a "
            "simplified portfolio risk score."
        )

        st.markdown("### 🧪 Run Scenarios")

        st.write(
            "Change investment amounts and risk profiles "
            "to see how hypothetical historical outcomes "
            "would have changed."
        )

        st.markdown("### 📊 Compare Decisions")

        st.write(
            "Use historical data to explore how different "
            "portfolio allocations behaved under the same "
            "market conditions."
        )

    st.divider()

    # -----------------------------------------------------
    # HOW IT WORKS
    # -----------------------------------------------------

    st.subheader("How PortfolioLab Works")

    st.write(
        "PortfolioLab follows a simple analytical process:"
    )

    step1, step2, step3, step4 = st.columns(4)

    with step1:

        st.markdown("### 01")

        st.write(
            "**Select a portfolio**"
        )

        st.caption(
            "Choose a risk profile and investment amount."
        )

    with step2:

        st.markdown("### 02")

        st.write(
            "**Pull market data**"
        )

        st.caption(
            "Historical ETF prices are retrieved through "
            "Yahoo Finance."
        )

    with step3:

        st.markdown("### 03")

        st.write(
            "**Calculate results**"
        )

        st.caption(
            "Daily returns are combined according to "
            "the portfolio's allocation."
        )

    with step4:

        st.markdown("### 04")

        st.write(
            "**Analyze the portfolio**"
        )

        st.caption(
            "Performance, risk, allocation, and scenarios "
            "are presented visually."
        )

    st.divider()

    # -----------------------------------------------------
    # METHODOLOGY
    # -----------------------------------------------------

    st.subheader("Methodology")

    methodology_col1, methodology_col2 = st.columns(2)

    with methodology_col1:

        st.markdown("### Portfolio Returns")

        st.write(
            "Daily portfolio returns are calculated by "
            "multiplying each ETF's daily return by its "
            "assigned portfolio weight and summing the results."
        )

        st.markdown("### Volatility")

        st.write(
            "Annualized volatility is estimated from the "
            "standard deviation of daily portfolio returns "
            "using 252 trading days per year."
        )

    with methodology_col2:

        st.markdown("### Maximum Drawdown")

        st.write(
            "Maximum drawdown measures the largest historical "
            "decline from a previous portfolio peak."
        )

        st.markdown("### Benchmark")

        st.write(
            "VOO is used as a simplified S&P 500 benchmark "
            "for comparing portfolio performance."
        )

    st.divider()

    # -----------------------------------------------------
    # TECHNOLOGY
    # -----------------------------------------------------

    st.subheader("Built With")

    tech1, tech2, tech3, tech4 = st.columns(4)

    with tech1:

        st.markdown("### Python")

        st.caption(
            "Core calculations and data processing"
        )

    with tech2:

        st.markdown("### Streamlit")

        st.caption(
            "Interactive web application"
        )

    with tech3:

        st.markdown("### Pandas")

        st.caption(
            "Financial data analysis"
        )

    with tech4:

        st.markdown("### yfinance")

        st.caption(
            "Historical market data"
        )

    st.divider()

    # -----------------------------------------------------
    # IMPORTANT LIMITATIONS
    # -----------------------------------------------------

    st.subheader("Important Limitations")

    st.warning(
        "PortfolioLab is an educational project and does "
        "not provide investment advice."
    )

    st.write(
        "Historical performance is not a guarantee of future "
        "results. The portfolio simulations do not account "
        "for taxes, trading costs, bid-ask spreads, dividends "
        "being paid out separately, or changes in portfolio "
        "weights over time."
    )

    st.write(
        "Risk measurements are simplified educational metrics "
        "and should not be interpreted as professional investment "
        "recommendations."
    )

    st.divider()

    # -----------------------------------------------------
    # PROJECT PHILOSOPHY
    # -----------------------------------------------------

    st.subheader("The Idea Behind PortfolioLab")

    st.markdown(
        """
        > **Don't just tell me what to invest in.  
        > Help me understand why.**
        """
    )

    st.write(
        "PortfolioLab is built around the idea that financial "
        "literacy improves when investors can experiment, "
        "compare outcomes, and understand the assumptions "
        "behind the numbers."
    )
# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "PortfolioLab · Educational portfolio analytics project"
)

st.caption(
    "Historical market data provided through Yahoo Finance "
    "via yfinance. This application does not provide "
    "personalized investment advice."
)
