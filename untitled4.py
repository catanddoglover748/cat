import streamlit as st

st.title("こんにちは！")
st.write("初めまして。これは最初のStreamlitアプリです。")
import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# タイトル
st.title("📈 株価チャート＆AI予測デモ")

# 株価コードの入力
ticker = st.text_input("ティッカーシンボルを入力してください（例：AAPL, MSFT, TSLA）", "AAPL")

# 日付範囲の選択
days = st.slider("何日分のデータを表示しますか？", 30, 365, 180)

# データ取得
if ticker:
    end_date = datetime.today()
    start_date = end_date - timedelta(days=days)

    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        st.write(f"表示中：{ticker} の株価データ（{start_date.date()}～{end_date.date()}）")

        # チャート表示
        fig, ax = plt.subplots()
        ax.plot(data.index, data['Close'], label='終値')
        ax.set_title(f"{ticker} 株価チャート")
        ax.set_xlabel("日付")
        ax.set_ylabel("価格（USD）")
        ax.legend()
        st.pyplot(fig)

    except Exception as e:
        st.error(f"データ取得に失敗しました: {e}")
