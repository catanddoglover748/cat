# =============================
# 1. 必要なライブラリのインポート（ファイルの先頭）
# =============================
import streamlit as st
import yfinance as yf
import finnhub
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

# =============================
# 2. Finnhub APIクライアントの初期化（インポートのすぐ下）
# =============================
st.set_page_config(layout="wide")
api_key = st.secrets["FINNHUB_API_KEY"]
finnhub_client = finnhub.Client(api_key=api_key)

# ----------------------------
# 📌 1. ページタイトル
# ----------------------------
st.title("📊 株価チャートビューア（TradingView風）")

# ----------------------------
# 📌 2. ティッカーとセッション管理
# ----------------------------
ticker_list = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "NVDA", "AMD", "NFLX", "COIN"]

if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = ticker_list[0]

# どのセクションでも使えるように先に確定
ticker = st.session_state.selected_ticker

# ----------------------------
# 📌 3. 画面を2カラムに分割
# ----------------------------
col1, col2 = st.columns([1, 4])

# ----------------------------
# 📌 4. 左：ティッカー選択ボタン（TradingView風）
# ----------------------------
with col1:
    st.markdown("### ティッカー選択")
    for t in ticker_list:
        if st.button(t, use_container_width=True):
            st.session_state.selected_ticker = t
            ticker = t  # 即時反映

# ----------------------------
# 📌 5. 右：チャートと操作パネル
# ----------------------------
with col2:
    st.markdown(f"## 選択中: `{ticker}`")

    period = st.selectbox(
        "表示期間を選んでください",
        ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"),
        index=2
    )

    # データ取得・チャート描画
    try:
        data = yf.Ticker(ticker).history(period=period)
        if not data.empty:
            # 移動平均線
            data["SMA20"] = data["Close"].rolling(window=20).mean()
            data["SMA50"] = data["Close"].rolling(window=50).mean()
            data["SMA200"] = data["Close"].rolling(window=200).mean()

            fig = go.Figure(
                data=[
                    go.Candlestick(
                        x=data.index,
                        open=data["Open"],
                        high=data["High"],
                        low=data["Low"],
                        close=data["Close"],
                        increasing_line_color="green",
                        decreasing_line_color="red",
                        name="ローソク足",
                    )
                ]
            )

            fig.add_trace(
                go.Scatter(x=data.index, y=data["SMA20"], mode="lines", name="SMA 20日",
                           line=dict(color="blue", width=1))
            )
            fig.add_trace(
                go.Scatter(x=data.index, y=data["SMA50"], mode="lines", name="SMA 50日",
                           line=dict(color="red", width=1))
            )
            fig.add_trace(
                go.Scatter(x=data.index, y=data["SMA200"], mode="lines", name="SMA 200日",
                           line=dict(color="purple", width=1))
            )

            fig.update_layout(
                title=f"{ticker} ローソク足 + SMA",
                xaxis_title="日付",
                yaxis_title="価格 (USD)",
                xaxis_rangeslider_visible=False,
                height=600,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ データが取得できませんでした。")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

# ------------------------------------------
# 📊 決算サマリー表示（チャートの下）
# ------------------------------------------
st.markdown("---")
st.subheader("📋 決算概要")

# ========= ⏬ APIから決算データ取得（自動換算対応） =========
# 売上は B(十億USD) で統一表示
def safe_pct(numer, denom):
    try:
        if denom and denom != 0:
            return round((numer - denom) / denom * 100, 2)
    except Exception:
        pass
    return 0.0

def to_billions(v):
    try:
        return float(v) / 1e9
    except Exception:
        return 0.0

eps_actual = eps_est = 0.0
rev_actual_B = rev_est_B = 0.0
eps_diff_pct = rev_diff_pct = 0.0
next_eps_est = "TBD"
next_rev_B = next_rev_diff_pct = 0.0
annual_eps = "TBD"
annual_rev_B = "TBD"

try:
    # 直近決算（company_earnings）
    earnings_list = finnhub_client.company_earnings(ticker, limit=1)
    earnings = earnings_list[0] if isinstance(earnings_list, list) and earnings_list else {}

    # 基本メトリクス
    bf = finnhub_client.company_basic_financials(ticker, "all")
    metrics = bf.get("metric", {}) if isinstance(bf, dict) else {}

    shares_outstanding = metrics.get("sharesOutstanding", 0) or 0

    # 実売上（financials_reported）
    # 構造: financials["data"][0]["report"]["ic"]["Revenue"]
    financials = finnhub_client.financials_reported(symbol=ticker, freq="quarterly")
    report_data = financials.get("data", []) if isinstance(financials, dict) else []
    if report_data and isinstance(report_data[0], dict):
        report = report_data[0].get("report", {})
        ic = report.get("ic", {}) if isinstance(report, dict) else {}
        rev_actual_raw = ic.get("Revenue")  # 単位: USD
        rev_actual_B = to_billions(rev_actual_raw)

    # 予想売上（自動換算）
    # 優先順: revenuePerShareForecast > revenuePerShare > revenuePerShareTTM
    rps_fore = metrics.get("revenuePerShareForecast")
    rps = metrics.get("revenuePerShare")
    rps_ttm = metrics.get("revenuePerShareTTM")

    rps_used = None
    for cand in (rps_fore, rps, rps_ttm):
        if isinstance(cand, (int, float)) and cand > 0:
            rps_used = cand
            break

    if rps_used and shares_outstanding:
        rev_est_B = (rps_used * shares_outstanding) / 1e9

    # EPS 実績/予想
    eps_actual = float(earnings.get("actual", 0) or 0)
    eps_est = float(earnings.get("estimate", 0) or 0)
    eps_diff_pct = safe_pct(eps_actual, eps_est)

    # 次回予想 EPS / 売上
    # Finnhubのキー名はアカウント/銘柄で異なることがあるため複数候補を参照
    next_eps_est = (
        metrics.get("nextEarningsPerShare")
        or metrics.get("epsNextQuarter")
        or "TBD"
    )

    rps_next = metrics.get("revenuePerShareForecast")
    if rps_next and shares_outstanding:
        next_rev_B = (rps_next * shares_outstanding) / 1e9
        next_rev_diff_pct = safe_pct(next_rev_B, rev_actual_B)

    # 年間予想/TTM（売上は B 換算）
    annual_eps = (
        metrics.get("epsInclExtraItemsAnnual")
        or metrics.get("epsInclExtraItemsTTM")
        or "TBD"
    )
    if rps_ttm and shares_outstanding:
        annual_rev_B = round((rps_ttm * shares_outstanding) / 1e9, 2)
    else:
        annual_rev_B = "TBD"

    # 乖離率
    rev_diff_pct = safe_pct(rev_actual_B, rev_est_B)

except Exception as e:
    st.warning(f"⚠️ 決算データの取得で例外が発生しました: {e}")

# ==== 表示 ====
col_a, col_b = st.columns(2)

with col_a:
    st.metric("EPS (Actual)", f"{eps_actual}", f"{eps_diff_pct:+.2f}%")
    st.metric("Next Qtr EPS (Est.)", f"{next_eps_est}")
    st.metric("Annual EPS (Est.)", f"{annual_eps}")

with col_b:
    st.metric("Revenue (B, Actual)", f"{rev_actual_B:.2f}B", f"{rev_diff_pct:+.2f}%")
    st.metric("Next Qtr Revenue (Est.)", f"{next_rev_B:.2f}B", f"{next_rev_diff_pct:+.2f}%")
    st.metric("Annual Revenue (TTM, Est.)", f"{annual_rev_B}")

# ------------------------------------------
# 🎯 ターゲット価格のサンプル（必要ならAPI接続に差し替え）
# ------------------------------------------
price_data = pd.DataFrame({
    "Label": ["Before", "After", "Analyst Target", "AI Target"],
    "Price": [181.75, 176.36, 167.24, 178.20]
})

fig_price = px.bar(
    price_data, x="Price", y="Label", orientation="h", text="Price",
    color="Label",
    color_discrete_map={
        "Before": "lightblue",
        "After": "green",
        "Analyst Target": "orange",
        "AI Target": "red",
    }
)
fig_price.update_layout(
    title="Stock & Target Prices",
    xaxis_title="価格 (USD)",
    yaxis_title="",
    height=400,
)
st.plotly_chart(fig_price, use_container_width=True)

# ------------------------------------------
# 🤖 AI Rating（仮置き）
# ------------------------------------------
st.markdown("### 🤖 AI Rating: 📈")
st.caption("*Earnings report released on 2025-08-27. Informational purposes only. Please consult with a professional before investing.*")
