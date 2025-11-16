import streamlit as st
import requests
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import plotly.graph_objs as go
import yfinance as yf
import base64
import json
import os
from io import StringIO
from datetime import date

try:
    from nsepy import get_history
except ImportError:
    st.warning("nsepy not installed. Run `pip install nsepy` for best Indian stock experience.")

API_KEY = '84626b8618a3fa8d2191d6247c679b76'  # Replace with your real Marketstack key

# --- Merge CSVs for stock symbols (US, India, Japan) ---
US_CSV = 'symbols.csv'
INDIA_CSV = 'Indian_stocks.csv'
JAPAN_CSV = 'Japan_stocks.csv'  # Optional
SYMBOLS_CSV = 'symbols.csv'

def adapt_and_load(file_path, name_col_candidates, symbol_col_candidates, add_ns_suffix=False):
    df = pd.read_csv(file_path)
    df.columns = [col.strip().capitalize() for col in df.columns]
    symbol_col = None
    shortname_col = None
    for c in symbol_col_candidates:
        if c in df.columns:
            symbol_col = c
            break
    for c in name_col_candidates:
        if c in df.columns:
            shortname_col = c
            break
    if symbol_col and shortname_col:
        df = df.rename(columns={symbol_col: "Symbol", shortname_col: "Shortname"})
        if add_ns_suffix:
            df["Symbol"] = df["Symbol"].astype(str) + ".NS"
        return df[["Symbol", "Shortname"]]
    else:
        raise ValueError(f"Could not find required columns in {file_path}: symbol={symbol_col}, name={shortname_col}")

def merge_csvs(us_csv, india_csv, japan_csv, out_csv):
    try:
        us_df = adapt_and_load(us_csv, name_col_candidates=["Shortname","Name"], symbol_col_candidates=["Symbol","Ticker"])
        india_df = adapt_and_load(india_csv, name_col_candidates=["Name of company","Shortname","Company"], symbol_col_candidates=["Symbol"], add_ns_suffix=True)
        dfs = [us_df, india_df]
        if os.path.exists(japan_csv):
            japan_df = adapt_and_load(japan_csv, name_col_candidates=["Name","Shortname","Company"], symbol_col_candidates=["Symbol","Code","Ticker"])
            dfs.append(japan_df)
        merged_df = pd.concat(dfs, ignore_index=True)
        merged_df = merged_df.drop_duplicates(subset=["Symbol"], keep="first")
        merged_df.to_csv(out_csv, index=False)
    except Exception as e:
        st.error(f"Error merging stock symbol CSV files: {e}")

merge_csvs(US_CSV, INDIA_CSV, JAPAN_CSV, SYMBOLS_CSV)

WATCHLIST_FILE = "watchlist.json"

symbols_df = pd.read_csv(SYMBOLS_CSV)

def load_watchlist_state():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r") as f:
            data = json.load(f)
            return data.get("watchlist", ["AAPL", "TSLA"]), set(data.get("favorites", []))
    else:
        return ["AAPL", "TSLA"], set()

def save_watchlist_state(watchlist, favorites):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump({"watchlist": watchlist, "favorites": list(favorites)}, f)

if "page" not in st.session_state:
    st.session_state.page = "splash"
if "watchlist" not in st.session_state or "favorites" not in st.session_state:
    wl, fv = load_watchlist_state()
    st.session_state.watchlist = wl
    st.session_state.favorites = fv
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = ""
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def get_theme_colors(mode):
    if mode == "dark":
        BG_COLOR = "#181c2f"
        CARD_BG = "#232738"
        TEXT = "#f7f9fb"
        ACCENT = "#5076ee"
        SUBTEXT = "#b5d0ff"
        GRID = "#35374b"
    else:
        BG_COLOR = "#f7f9fb"
        CARD_BG = "#ffffff"
        TEXT = "#232738"
        ACCENT = "#5076ee"
        SUBTEXT = "#0b2578"
        GRID = "#dde4f0"
    return BG_COLOR, CARD_BG, TEXT, ACCENT, SUBTEXT, GRID

BG_COLOR, CARD_BG, TEXT_WHITE, ACCENT_BLUE, TEXT_ACCENT, GRID_COLOR = get_theme_colors(st.session_state.theme)
GREEN = "#1cbb68"
RED = "#fa3742"

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {BG_COLOR} !important;
        color: {TEXT_WHITE} !important;
    }}
    .title-text {{
        color: {ACCENT_BLUE};
        text-align:center;
        font-weight:700;
        font-size:2.3rem;
        margin-top:18px;
    }}
    .subtitle-text {{
        color: {TEXT_ACCENT};
        text-align:center;
        font-weight:500;
        font-size:1rem;
        margin-bottom:10px;
    }}
    .card-container {{
        background-color: {CARD_BG};
        color: {TEXT_WHITE};
        border-radius:8px;
        box-shadow:0 3px 10px #5076ee55;
        padding:14px;
        margin-bottom:10px;
        text-align:center;
        font-size:0.95rem;
    }}
    .stTextInput>div>div>input {{
        border:2px solid {ACCENT_BLUE} !important;
        background-color:{CARD_BG} !important;
        color:{TEXT_WHITE} !important;
        font-weight:600;
    }}
    .stButton>button {{
        background-color: {ACCENT_BLUE} !important;
        color: {TEXT_WHITE} !important;
        border-radius:8px !important;
        font-size:1rem !important;
        font-weight:600 !important;
        margin: 2px 2px;
        min-width:70px;
    }}
    .stMetric {{
        color: {TEXT_WHITE} !important;
        font-size:1rem;
    }}
    .stSelectbox div[role="listbox"] {{
        background:{CARD_BG} !important;
        color:{TEXT_WHITE} !important;
    }}
    </style>
""", unsafe_allow_html=True)

# -------- Splash Page --------
if st.session_state.page == "splash":
    st.markdown(
        f"""<div style='height:350px;display:flex;align-items:center;justify-content:center;'>
            <span style='font-size:90px;'>{'📈'}</span>
        </div>
        <h1 class='title-text'>Welcome to Stock Price Predictor</h1>
        <h4 class='subtitle-text'>Forecast | Watch | Analyze </h4>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Enter App ▶️", key="goto_home"):
        st.session_state.page = "home"
        st.rerun()

# -------- Home Page ---------
elif st.session_state.page == "home":
    theme_col, _ = st.columns([1, 4])
    with theme_col:
        if st.button("🌞" if st.session_state.theme == "dark" else "🌚", help="Toggle Theme"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()

    BG_COLOR, CARD_BG, TEXT_WHITE, ACCENT_BLUE, TEXT_ACCENT, GRID_COLOR = get_theme_colors(st.session_state.theme)
    st.markdown("<h1 class='title-text'>Stock Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<h4 class='subtitle-text'>Search stocks by name/symbol; add to watchlist and analyze</h4>", unsafe_allow_html=True)
    st.markdown(f"<hr style='margin-top:6px;margin-bottom:14px;background:{GRID_COLOR};'>", unsafe_allow_html=True)

    search_query = st.text_input("🔎 Search company or ticker (e.g. Apple, Reliance, AAPL, RELIANCE.NS):", key="search_bar")
    found_match = False
    selected_symbol = ""

    if search_query.strip():
        matches = symbols_df[
            symbols_df['Shortname'].str.contains(search_query, case=False, na=False) |
            symbols_df['Symbol'].str.contains(search_query, case=False, na=False)
        ]
        if len(matches):
            st.write("**Select company below for analysis:**")
            for idx, row in matches.iterrows():
                sym = row['Symbol']
                btn_lab = f"{row['Shortname']} ({sym})"
                if st.button(btn_lab, key=f"search_{sym}_{idx}"):
                    st.session_state.selected_ticker = sym
                    selected_symbol = sym
                    found_match = True
                    st.rerun()
        else:
            st.warning("No companies found. Try another name or symbol.")

    if st.session_state.selected_ticker and st.session_state.selected_ticker not in st.session_state.watchlist:
        sym = st.session_state.selected_ticker
        label = symbols_df[symbols_df['Symbol'] == sym]['Shortname'].values[0] if sym in symbols_df['Symbol'].values else sym
        if st.button(f"➕ Add {label} ({sym}) to Watchlist"):
            st.session_state.watchlist.append(sym)
            save_watchlist_state(st.session_state.watchlist, st.session_state.favorites)
            st.rerun()

    st.markdown("#### Your Watchlist")
    for sym in sorted(st.session_state.watchlist, key=lambda x: (x not in st.session_state.favorites, x)):
        wcol1, wcol2, wcol3 = st.columns([8, 2, 2])
        with wcol1:
            stock_name = symbols_df[symbols_df['Symbol'] == sym]
            name_label = f"{stock_name.iloc[0]['Shortname']}" if not stock_name.empty else sym
            star = "⭐" if sym in st.session_state.favorites else "☆"
            if st.button(f"{star} {name_label} ({sym})", key=f"watch_{sym}"):
                st.session_state.selected_ticker = sym
                st.rerun()
        with wcol2:
            if st.button("★" if sym in st.session_state.favorites else "☆", key=f"fav_{sym}"):
                if sym in st.session_state.favorites:
                    st.session_state.favorites.remove(sym)
                else:
                    st.session_state.favorites.add(sym)
                save_watchlist_state(st.session_state.watchlist, st.session_state.favorites)
                st.rerun()
        with wcol3:
            if st.button(f"❌", key=f"remove_{sym}"):
                st.session_state.watchlist.remove(sym)
                st.session_state.favorites.discard(sym)
                save_watchlist_state(st.session_state.watchlist, st.session_state.favorites)
                if st.session_state.selected_ticker == sym:
                    st.session_state.selected_ticker = ""
                st.rerun()

    st.markdown(f"<hr style='margin-top:10px;margin-bottom:16px;background:{GRID_COLOR};'>", unsafe_allow_html=True)

    if st.session_state.selected_ticker:
        if st.button("⬇️ Download Recent Data (CSV)"):
            symbol = st.session_state.selected_ticker
            df = pd.DataFrame()
            if symbol.endswith(".NS"):
                df = yf.download(symbol, period="60d", interval="1d")
                if df.empty and "get_history" in globals():
                    nse_symbol = symbol.replace(".NS", "")
                    df = get_history(symbol=nse_symbol, start=date(2024,1,1), end=date.today())
                    df.reset_index(inplace=True)
                    df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume", "Date": "date"}, inplace=True)
            else:
                url = f"http://api.marketstack.com/v1/eod?access_key={API_KEY}&symbols={symbol}"
                res = requests.get(url)
                data = res.json()
                df = pd.DataFrame(data["data"]).sort_values(by="date").tail(60) if "data" in data and data["data"] else pd.DataFrame()
            if not df.empty:
                csv_buf = StringIO()
                df.to_csv(csv_buf, index=False)
                b64 = base64.b64encode(csv_buf.getvalue().encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="price_{symbol}.csv">Download CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                st.warning("No data found to download.")

    ticker_to_analyze = st.session_state.selected_ticker
    if ticker_to_analyze:
        st.markdown(f"### Analysis for {ticker_to_analyze}")

        df = pd.DataFrame()
        if ticker_to_analyze.endswith(".NS"):
            df = yf.download(ticker_to_analyze, period="200d", interval="1d")
            if df.empty and "get_history" in globals():
                nse_symbol = ticker_to_analyze.replace(".NS", "")
                df = get_history(symbol=nse_symbol, start=date(2024,1,1), end=date.today())
                df.reset_index(inplace=True)
                df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume", "Date": "date"}, inplace=True)
            else:
                df = df.reset_index()
                df = df.rename(columns={"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
            df = df.sort_values(by="date").tail(200)
        else:
            url = f"http://api.marketstack.com/v1/eod?access_key={API_KEY}&symbols={ticker_to_analyze}"
            res = requests.get(url)
            data = res.json()
            if "data" in data and data["data"]:
                df = pd.DataFrame(data["data"])
                df = df.sort_values(by="date").tail(200)

        if not df.empty and "close" in df and not df["close"].empty:
            latest_close = float(df["close"].iloc[-1]) if not df["close"].empty else float("nan")
            latest_date = str(df["date"].iloc[-1]) if not df["date"].empty else "N/A"
            last_high = float(df["high"].iloc[-1]) if not df["high"].empty else float("nan")
            last_low = float(df["low"].iloc[-1]) if not df["low"].empty else float("nan")
            mcol1, mcol2, mcol3 = st.columns(3)
            mcol1.markdown(f"<div class='card-container'><b>Latest EOD</b><br>{latest_close:.2f} USD<br>{latest_date}</div>", unsafe_allow_html=True)
            mcol2.markdown(f"<div class='card-container'><b>Last High</b><br>{last_high:.2f} USD</div>", unsafe_allow_html=True)
            mcol3.markdown(f"<div class='card-container'><b>Last Low</b><br>{last_low:.2f} USD</div>", unsafe_allow_html=True)
            st.markdown(f"<hr style='margin-top:8px;margin-bottom:10px;background:{GRID_COLOR};'>", unsafe_allow_html=True)

            st.markdown("#### Indicators:")
            ind1, ind2, ind3, ind4 = st.columns(4)
            show_ma = ind1.checkbox("EMA(20)", value=True)
            show_boll = ind2.checkbox("BOLL", value=False)
            show_rsi = ind3.checkbox("RSI(14)", value=False)
            show_macd = ind4.checkbox("MACD", value=False)

            fig = go.Figure(data=[go.Candlestick(
                x=pd.to_datetime(df["date"]), open=df["open"], high=df["high"], low=df["low"], close=df["close"],
                increasing_line_color=GREEN, decreasing_line_color=RED, name="Candles"
            )])
            df['Close'] = df['close']

            if show_ma and len(df) >= 20:
                df["EMA20"] = df["Close"].ewm(span=20).mean()
                fig.add_trace(go.Scatter(x=df["date"], y=df["EMA20"], mode="lines", name="EMA20", line=dict(color=ACCENT_BLUE, width=2, dash="dot")))
            if show_boll and len(df) >= 20:
                ma = df["Close"].rolling(window=20).mean()
                std = df["Close"].rolling(window=20).std()
                upper = ma + 2*std
                lower = ma - 2*std
                fig.add_trace(go.Scatter(x=df["date"], y=upper, line=dict(color="#868686", width=1, dash="dash"), name='BOLL Upper'))
                fig.add_trace(go.Scatter(x=df["date"], y=lower, line=dict(color="#868686", width=1, dash="dash"), name='BOLL Lower'))
            if show_macd and len(df) >= 26:
                ema12 = df['Close'].ewm(span=12).mean()
                ema26 = df['Close'].ewm(span=26).mean()
                macd = ema12 - ema26
                signal = macd.ewm(span=9).mean()
                fig.add_trace(go.Scatter(x=df["date"], y=macd, name="MACD", line=dict(color="#9b30ff")))
                fig.add_trace(go.Scatter(x=df["date"], y=signal, name="MACD Signal", line=dict(color="#ffc125")))
            st.markdown("<h4 class='subtitle-text'>📊 Candlestick & Indicators</h4>", unsafe_allow_html=True)
            fig.update_layout(plot_bgcolor=BG_COLOR, paper_bgcolor=BG_COLOR,
                font=dict(color=TEXT_WHITE, size=15),
                xaxis=dict(title="Date", color=TEXT_WHITE, gridcolor=GRID_COLOR),
                yaxis=dict(title="Price (USD)", color=TEXT_WHITE, gridcolor=GRID_COLOR),
                margin=dict(l=20, r=20, t=35, b=15), showlegend=True)

            st.plotly_chart(fig, use_container_width=True)

            if show_rsi and len(df) > 14:
                delta = df['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - 100 / (1 + rs)
                rsi_fig = go.Figure()
                rsi_fig.add_trace(go.Scatter(x=df["date"], y=rsi, name='RSI(14)', line=dict(color="#00ffa2", width=2)))
                rsi_fig.update_layout(
                    title="Relative Strength Index",
                    plot_bgcolor=BG_COLOR, paper_bgcolor=BG_COLOR,
                    xaxis=dict(title="Date", color=TEXT_WHITE),
                    yaxis=dict(title="RSI", color=TEXT_WHITE, range=[0, 100]),
                    showlegend=True, margin=dict(l=20, r=20, t=30, b=18),
                    font=dict(color=TEXT_WHITE)
                )
                st.plotly_chart(rsi_fig, use_container_width=True)

            if len(df) > 20:
                df_recent = df.tail(20).reset_index(drop=True)
                X = np.arange(len(df_recent)).reshape(-1, 1)
                yarr = df_recent["close"].values
                model = LinearRegression()
                model.fit(X, yarr)
                next_day = np.array([[len(df_recent)]])
                pred_price = float(model.predict(next_day)[0])
                volatility = float(np.std(df_recent["close"]))
                risk_label = "✅ Low" if volatility < 20 else ("⚠️ Medium" if volatility < 50 else "❌ High")
                pred_col, vol_col = st.columns(2)
                pred_col.markdown(f"<div class='card-container'><b>Prediction</b><br>{pred_price:.2f} USD</div>", unsafe_allow_html=True)
                vol_col.markdown(f"<div class='card-container'><b>Risk / Volatility</b><br>{volatility:.2f}<br>{risk_label}</div>", unsafe_allow_html=True)
            else:
                st.warning("Not enough data for prediction.")
        else:
            st.error("No valid OHLCV data found. This sometimes happens for new or illiquid tickers, or if yfinance+NSEpy data was unavailable.")
    else:
        st.info("Search or select a stock/company above to analyze.")
