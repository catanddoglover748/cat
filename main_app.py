import streamlit as st
from data_fetcher import get_stock_data
from chart import show_line_chart, show_candlestick_chart  # ← 追加

st.title("📈 株価チャートアプリ（分離版）")

ticker = st.text_input("ティッカーを入力してください", "AAPL")
period = st.selectbox("期間", ["1mo", "3mo", "6mo", "1y", "5y", "max"], index=2)

chart_type = st.radio("チャート種類を選んでください", ["ラインチャート", "ローソク足チャート"])

if ticker:
    try:
        df = get_stock_data(ticker, period)
        if not df.empty:
            if chart_type == "ラインチャート":
                show_line_chart(df, ticker)
            else:
                show_candlestick_chart(df, ticker)
        else:
            st.warning("データが取得できませんでした。")
    except Exception as e:
        st.error(f"エラー: {e}")
