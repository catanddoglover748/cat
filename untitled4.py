# =============================
# 1. 必要なライブラリのインポート（ファイルの先頭）
# =============================
import streamlit as st
import yfinance as yf
import finnhub  
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from datetime import datetime, timedelta

# =============================
# 2. Finnhub APIクライアントの初期化（インポートのすぐ下）
# =============================

# Secrets からAPIキーを取得して Finnhubクライアントを初期化
api_key = st.secrets["FINNHUB_API_KEY"]
finnhub_client = finnhub.Client(api_key=api_key)

# ----------------------------
# 📌 1. ページタイトル
# ----------------------------
st.set_page_config(layout="wide")
st.title("📊 株価チャートビューア（TradingView風）")

# ----------------------------
# 📌 2. ティッカーとセッション管理
# ----------------------------
ticker_list = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "NVDA", "AMD", "NFLX", "COIN"]

# 初期ティッカー
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = ticker_list[0]

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
        if st.button(t):
            st.session_state.selected_ticker = t

# ----------------------------
# 📌 5. 右：チャートと操作パネル
# ----------------------------
with col2:
    ticker = st.session_state.selected_ticker
    st.markdown(f"## 選択中: `{ticker}`")

    # 表示期間選択
    period = st.selectbox("表示期間を選んでください",
                          ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"),
                          index=2)

    # データ取得・チャート描画
    try:
        data = yf.Ticker(ticker).history(period=period)
        if not data.empty:
            # 移動平均線の計算
            data['SMA20'] = data['Close'].rolling(window=20).mean()
            data['SMA50'] = data['Close'].rolling(window=50).mean()
            data['SMA200'] = data['Close'].rolling(window=200).mean()

            # Plotlyローソク足 + SMA
            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                increasing_line_color='green',
                decreasing_line_color='red',
                name="ローソク足"
            )])

            # 各SMA追加
            fig.add_trace(go.Scatter(x=data.index, y=data['SMA20'], mode='lines',
                                     name="SMA 20日", line=dict(color='blue', width=1)))
            fig.add_trace(go.Scatter(x=data.index, y=data['SMA50'], mode='lines',
                                     name="SMA 50日", line=dict(color='red', width=1)))
            fig.add_trace(go.Scatter(x=data.index, y=data['SMA200'], mode='lines',
                                     name="SMA 200日", line=dict(color='purple', width=1)))

            fig.update_layout(
                title=f"{ticker} ローソク足 + SMA",
                xaxis_title="日付",
                yaxis_title="価格 (USD)",
                xaxis_rangeslider_visible=False,
                height=600
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

# ========= ⏬ APIから決算データ取得（修正済・自動換算対応） =========
try:
    # earnings_list を明示的に定義
    earnings_list = finnhub_client.company_earnings(ticker, limit=1)
    metrics = finnhub_client.company_basic_financials(ticker, 'all')["metric"]

    # 実売上データ取得（financials_reportedから）
    financials = finnhub_client.financials_reported(symbol=ticker, freq='quarterly')
    report_data = financials["data"] if isinstance(financials, dict) and "data" in financials else []

    # earnings_list の構造チェックと代入
    if isinstance(earnings_list, list) and len(earnings_list) > 0 and isinstance(earnings_list[0], dict):
        earnings = earnings_list[0]
    else:
        st.warning("earnings データが dict 形式ではありません")
        earnings = {}

    # 実売上値（B単位）を取得
    rev_actual = 0
try:
    if report_data and isinstance(report_data[0], dict):
        latest_report = report_data[0]
        report_section = latest_report.get("report", {})
        if isinstance(report_section, dict):
            rev_actual_str = report_section.get("ic", {}).get("Revenue", None)
            rev_actual = float(rev_actual_str) / 1e9 if rev_actual_str else 0
    else:
        st.warning("report_data[0] は dict ではありません")
except Exception as e:
    st.warning(f"売上実績データ取得時のエラー: {e}")


    # earnings の内容をデバッグ表示（必要に応じて削除OK）
    st.json(earnings)

    # 予想売上（1株あたり → 全体換算）【自動化】
    shares_outstanding = metrics.get("sharesOutstanding", 0)
    rev_est_raw = metrics.get("revenuePerShare", 0)
    rev_est = rev_est_raw * shares_outstanding / 1e9 if rev_est_raw and shares_outstanding else 0
    rev_diff = round((rev_actual - rev_est) / rev_est * 100, 2) if rev_est else 0

    # EPS（実績・予想・差分）
    eps_actual = earnings.get("actual", 0)
    eps_est = earnings.get("estimate", 0)
    eps_diff = round((eps_actual - eps_est) / eps_est * 100, 2) if eps_est else 0

    # 次回予想EPS・売上【自動化】
    next_eps_est = metrics.get("nextEarningsPerShare", "TBD")

    next_rev_est_raw = metrics.get("revenuePerShareForecast", 0)
    next_rev = next_rev_est_raw * shares_outstanding / 1e9 if next_rev_est_raw and shares_outstanding else 0
    next_rev_diff = round((next_rev - rev_actual) / rev_actual * 100, 2) if rev_actual else 0

except Exception as e:
    st.warning(f"決算データの取得で例外が発生しました: {e}")

    # 年間予想
    annual_eps = metrics.get("epsInclExtraItemsAnnual", "TBD")
    annual_rev = metrics.get("revenuePerShareTTM", "TBD")

except Exception as e:
    st.warning(f"⚠️ 決算データの取得に失敗しました: {e}")
    eps_actual, eps_est, eps_diff = 0, 0, 0
    rev_actual, rev_est, rev_diff = 0, 0, 0
    next_eps_est, next_rev, next_rev_diff = "TBD", 0, 0
    annual_eps, annual_rev = "TBD", "TBD"




    # EPS & Revenue
    eps_actual = earnings.get("actual", 0)
    eps_est = earnings.get("estimate", 0)
    eps_diff = round((eps_actual - eps_est) / eps_est * 100, 2) if eps_est else 0

    #rev_actual_raw = earnings.get("revenue")
    #rev_est_raw = earnings.get("revenueEstimate")
    #rev_actual = rev_actual_raw / 1e9 if rev_actual_raw else 0
    #rev_est = rev_est_raw / 1e9 if rev_est_raw else 0
    #rev_diff = round((rev_actual - rev_est) / rev_est * 100, 2) if rev_est else 0

    # Next Qtr EPS/Revenue
    next_eps_est = metrics.get("nextEarningsPerShare", "TBD")
    next_rev_est = metrics.get("revenuePerShareForecast", 0)
    next_rev = next_rev_est * 1.0235 if next_rev_est else 0
    next_rev_diff = round((next_rev - next_rev_est) / next_rev_est * 100, 2) if next_rev_est else 0

    # 年間予想
    annual_eps = metrics.get("epsInclExtraItemsAnnual", "TBD")
    annual_rev = metrics.get("revenuePerShareTTM", "TBD")

except Exception as e:
    st.warning(f"⚠️ 決算データの取得に失敗しました: {e}")
    eps_actual, eps_est, eps_diff = 0, 0, 0
    rev_actual, rev_est, rev_diff = 0, 0, 0
    next_eps_est, next_rev, next_rev_diff = "TBD", 0, 0
    annual_eps, annual_rev = "TBD", "TBD"
# ======== 🔼🔼 ここまで自動取得 🔼🔼 ========

# ==== 表示 ====
col_a, col_b = st.columns(2)

with col_a:
    st.metric("EPS", f"{eps_actual}", f"{eps_diff:+.2f}%", delta_color="normal")
    st.metric("Next Qtr EPS (Est.)", f"{next_eps_est}")
    st.metric("Annual EPS (Est.)", f"{annual_eps}")

with col_b:
    st.metric("Revenue (B)", f"{rev_actual:.2f}B", f"{rev_diff:+.2f}%", delta_color="normal")
    st.metric("Next Qtr Revenue", f"{next_rev:.2f}B", f"{next_rev_diff:+.2f}%")
    st.metric("Annual Revenue (Est.)", f"{annual_rev}B")
# ターゲット価格のグラフ（Plotly棒グラフ）
import plotly.express as px
import pandas as pd

price_data = pd.DataFrame({
    "Label": ["Before", "After", "Analyst Target", "AI Target"],
    "Price": [181.75, 176.36, 167.24, 178.20]
})

fig_price = px.bar(price_data, x="Price", y="Label", orientation="h",
                   text="Price", color="Label",
                   color_discrete_map={
                       "Before": "lightblue",
                       "After": "green",
                       "Analyst Target": "orange",
                       "AI Target": "red"
                   })
fig_price.update_layout(
    title="Stock & Target Prices",
    xaxis_title="価格 (USD)",
    yaxis_title="",
    height=400
)
st.plotly_chart(fig_price, use_container_width=True)

# AI Rating（仮置き）
st.markdown("### 🤖 AI Rating: 📈")
st.caption("*Earnings report released on 2025-08-27. Informational purposes only. Please consult with a professional before investing.*")

