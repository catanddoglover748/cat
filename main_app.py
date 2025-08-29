import streamlit as st
from data_fetcher import get_stock_data  # ←ここが分離のポイント

st.title("📈 株価チャートアプリ（分離版）")

ticker = st.text_input("ティッカーを入力してください", "AAPL")
period = st.selectbox("期間", ["1mo", "3mo", "6mo", "1y", "5y", "max"], index=2)

if ticker:
    try:
        df = get_stock_data(ticker, period)
        if not df.empty:
            st.line_chart(df["Close"])
        else:
            st.warning("データが取得できませんでした。")
    except Exception as e:
        st.error(f"エラー: {e}")
