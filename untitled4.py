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
