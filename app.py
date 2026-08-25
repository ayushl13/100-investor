import streamlit as st
import yfinance as yf
import pandas as pd


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
        "role": "Core equity exposure"
    },

    "QQQ": {
        "name": "Invesco QQQ",
        "asset_class": "U.S. Equities",
        "focus": "Nasdaq-100 companies",
        "role": "Growth and technology exposure"
    },

    "VXUS": {
        "name": "Vanguard Total International Stock ETF",
        "asset_class": "International Equities",
        "focus": "Companies outside the United States",
        "role": "International diversification"
    },

    "BND": {
        "name": "Vanguard Total Bond Market ETF",
        "asset_class": "Fixed Income",
        "focus": "U.S. investment-grade bonds",
        "role": "Income and portfolio stability"
    }
}


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

    st.line_chart(
        overview_chart,
        height=400
    )

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

            st.write(
                f"{ticker} — "
                f"{weight * 100:.0f}%"
            )

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

        st.markdown(
            f"### {ticker}"
        )

        st.write(
            etf_information[ticker]["name"]
        )

        st.caption(
            etf_information[ticker]["role"]
        )

        st.write(
            etf_information[ticker]["focus"]
        )


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

    st.line_chart(
        portfolio_value,
        height=400
    )

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

    st.line_chart(
        comparison,
        height=400
    )

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

    st.line_chart(
        etf_close,
        height=400
    )

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

    st.line_chart(
        scenario_value,
        height=400
    )

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
