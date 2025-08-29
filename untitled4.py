import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.graph_objects as go

# タイトル
st.title(" 株価チャート＆ローソク足ビューア")

# ティッカー入力と期間指定
# ウォッチリストを左に一覧表示する
ticker_list = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "NVDA", "AMD", "NFLX", "COIN"]
ticker = st.sidebar.radio("ティッカーを選んでください", ticker_list)


days = st.slider("何日分のデータを表示しますか？", 30, 365, 180)

period_choice = st.selectbox("表示期間（ローソク足用）", 
                             ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"), 
                             index=2, key="period_select")

# データ取得
if ticker:
    try:
        # 終値とmatplotlibグラフ用データ
        end_date = datetime.today()
        start_date = end_date - timedelta(days=days)
        data_raw = yf.download(ticker, start=start_date, end=end_date)

        st.subheader("📈 終値チャート（matplotlib）")
        fig, ax = plt.subplots()
        ax.plot(data_raw.index, data_raw['Close'], label='終値')
        ax.set_title(f"{ticker} の終値チャート")
        ax.set_xlabel("日付")
        ax.set_ylabel("価格（USD）")
        ax.legend()
        st.pyplot(fig)

        st.subheader("📊 終値チャート（Streamlit内蔵 line_chart）")
        st.line_chart(data_raw['Close'])

        # ローソク足チャート
        st.subheader(f"🕯️ ローソク足チャート（{period_choice}）")
        data_candle = yf.Ticker(ticker).history(period=period_choice)
        fig_candle = go.Figure(data=[go.Candlestick(
            x=data_candle.index,
            open=data_candle['Open'],
            high=data_candle['High'],
            low=data_candle['Low'],
            close=data_candle['Close'],
            increasing_line_color='green',
            decreasing_line_color='red'
        )])
        fig_candle.update_layout(
            xaxis_title='日付',
            yaxis_title='価格',
            xaxis_rangeslider_visible=False
        )
        st.plotly_chart(fig_candle, use_container_width=True)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")

import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.title(" ローソク足チャートビューア")

# ユーザー入力
ticker_list = ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "NVDA", "AMD", "NFLX", "COIN"]

ticker = st.selectbox("ウォッチリストからティッカーを選んでください", ticker_list, index=0)


period = st.selectbox("表示期間を選んでください",
                      ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"),
                      index=2)

# 株価データの取得とチャート表示
if ticker:
    try:
        data = yf.Ticker(ticker).history(period=period)
        if not data.empty:
            st.subheader(f"{ticker} のローソク足チャート（{period}）")

            fig = go.Figure(data=[go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                increasing_line_color='green',
                decreasing_line_color='red'
            )])

            fig.update_layout(
                xaxis_title='日付',
                yaxis_title='価格（USD）',
                xaxis_rangeslider_visible=False
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("データが取得できませんでした。ティッカーを確認してください。")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
# ...前略...
fig = go.Figure(data=[go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    increasing_line_color='green',
    decreasing_line_color='red'
)])

# SMAの計算と追加
data['SMA20'] = data['Close'].rolling(window=20).mean()
data['SMA50'] = data['Close'].rolling(window=50).mean()
data['SMA200'] = data['Close'].rolling(window=200).mean()


fig.add_trace(go.Scatter(
    x=data.index,
    y=data['SMA20'],
    mode='lines',
    line=dict(color='blue', width=1),
    name='SMA 20日'
))
# SMA50（赤）
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['SMA50'],
    mode='lines',
    line=dict(color='red', width=1),
    name='SMA 50日'
))

# SMA200（紫）
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['SMA200'],
    mode='lines',
    line=dict(color='purple', width=1),
    name='SMA 200日'
))

