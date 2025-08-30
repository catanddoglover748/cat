import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

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

# 仮のデータ（画像を参考に）
eps_actual = 1.04
eps_est = 1.01
eps_diff = round((eps_actual - eps_est) / eps_est * 100, 2)

rev_actual = 46.74
rev_est = 46.13
rev_diff = round((rev_actual - rev_est) / rev_est * 100, 2)

next_eps_est = 1.19
next_rev_est = 52.76
next_rev = 54.00
next_rev_diff = round((next_rev - next_rev_est) / next_rev_est * 100, 2)

# 2列構成で表示
col_a, col_b = st.columns(2)

with col_a:
    st.metric("EPS", f"{eps_actual}", f"{eps_diff:+.2f}%", delta_color="normal")
    st.metric("Next Qtr EPS (Est.)", f"{next_eps_est}")
    st.metric("Annual EPS (Est.)", "4.37")

with col_b:
    st.metric("Revenue (B)", f"{rev_actual}B", f"{rev_diff:+.2f}%", delta_color="normal")
    st.metric("Next Qtr Revenue", f"{next_rev}B", f"{next_rev_diff:+.2f}%")
    st.metric("Annual Revenue (Est.)", "203.4B")

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

