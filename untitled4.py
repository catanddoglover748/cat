import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import plotly.graph_objects as go

# タイトル
st.title("📊 株価チャート＆ローソク足ビューア")

# ティッカー入力と期間指定
ticker = st.text_input("ティッカーシンボルを入力してください（例：AAPL, MSFT, TSLA）", "AAPL")
days = st.slider("何日分のデータを表示しますか？", 30, 365, 180)
period_choice = st.selectbox("表示期間（ローソク足用）", ("1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"), index=2)

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

