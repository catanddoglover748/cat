# =============================
# 1. 必要なライブラリのインポート（ファイルの先頭）
# =============================
import streamlit as st
import yfinance as yf
import finnhub
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

import traceback

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
#st.title("📊 株価チャートビューア（TradingView風）")
st.title("""
<div class="tenet-h1"> 株価チャートビューア</div>
""", unsafe_allow_html=True)
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
st.markdown("""
<div class="tenet-h1"> 決算概要</div>
""", unsafe_allow_html=True)
if False:
    company = yf.Ticker(ticker).info.get("shortName", ticker)
    pe  = yf.Ticker(ticker).info.get("trailingPE", None)
    fpe = yf.Ticker(ticker).info.get("forwardPE", None)
    peg = yf.Ticker(ticker).info.get("pegRatio", None)
    mcap= yf.Ticker(ticker).info.get("marketCap", None)
    
    def human_mc(n):
        if not n: return "N/A"
        for u in ["","K","M","B","T"]: 
            if abs(n) < 1000: return f"{n:,.2f}{u}"
            n/=1000
        return f"{n:,.2f}Q"
    
    st.markdown(f"""
    <div class="card">
      <div class="header">
        <div class="logo">🟢</div>
        <div class="title-wrap">
          <div class="tenet-h1">{company}</div>
          <div class="tenet-h2">${ticker} Latest Earnings</div>
        </div>
      </div>
      <div class="kv">
        <span class="tenet-chip">Market Cap: <b>{human_mc(mcap)}</b></span>
        <span class="tenet-chip">P/E: <b>{f"{pe:.2f}" if isinstance(pe,(int,float)) else "N/A"}</b></span>
        <span class="tenet-chip">Forward P/E: <b>{f"{fpe:.2f}" if isinstance(fpe,(int,float)) else "N/A"}</b></span>
        <span class="tenet-chip">PEG: <b>{f"{peg:.2f}" if isinstance(peg,(int,float)) else "N/A"}</b></span>
      </div>
    """, unsafe_allow_html=True)


# ========= ⏬ 決算データ（自動換算・堅牢版） =========
DEBUG = True  # デバッグ時 True, 運用時 False

try:
    def safe_pct(numer, denom):
        try:
            if denom and float(denom) != 0:
                return round((float(numer) - float(denom)) / float(denom) * 100, 2)
        except Exception:
            pass
        return 0.0
    
    def to_billions(v):
        try:
            return float(v) / 1e9
        except Exception:
            return 0.0
    
    def get_shares_outstanding(metrics: dict, ticker: str) -> float:
        return (
            metrics.get("sharesOutstanding")
            or metrics.get("shareOutstanding")   # ← Finnhubではこちらが入ることが多い
            or yf.Ticker(ticker).info.get("sharesOutstanding")
            or 0.0
        )
    def _to_float(x):
        """カンマ付きや文字列もできるだけ float 化"""
        try:
            if isinstance(x, str):
                x = x.replace(",", "").strip()
            return float(x)
        except Exception:
            return None
    
    def extract_ic_number(ic):
        """
        financials_reported の report.ic から Revenue を抽出。
        ic が dict でも list でも、全要素を走査して候補キー/ラベルを探す。
        """
        if not ic:
            return None
    
        CANDS = (
            "Revenue",
            "TotalRevenue",
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "Total revenue",
            "Total Revenues",
            "Revenues",
        )
    
        # dict のときはキー優先
        if isinstance(ic, dict):
            for k in CANDS:
                v = ic.get(k)
                f = _to_float(v)
                if f is not None:
                    return f
    
        # list のときは全要素をチェック（先頭だけでなく）
        if isinstance(ic, list):
            for row in ic:
                if not isinstance(row, dict):
                    continue
                # 1) 候補キーがそのままある
                for k in CANDS:
                    if k in row:
                        f = _to_float(row[k])
                        if f is not None:
                            return f
                # 2) ラベル/コンセプトに含まれる
                label = str(
                    row.get("label")
                    or row.get("concept")
                    or row.get("name")
                    or ""
                ).lower()
                val = row.get("value") or row.get("val") or row.get("amount")
                for k in CANDS:
                    if k.lower() in label:
                        f = _to_float(val)
                        if f is not None:
                            return f
        return None
    
    # 初期化
    eps_actual = eps_est_val = 0.0
    eps_diff_pct = 0.0
    rev_actual_B = rev_est_B = 0.0
    next_eps_est = "TBD"
    next_rev_B = next_rev_diff_pct = 0.0
    annual_eps = "TBD"
    annual_rev_B = "TBD"
    
    # 1) EPS・売上（まず company_earnings を優先）
    earnings_list = finnhub_client.company_earnings(ticker, limit=1)
    if isinstance(earnings_list, list) and earnings_list and isinstance(earnings_list[0], dict):
        e0 = earnings_list[0]
    
        # EPS
        eps_actual  = _to_float(e0.get("actual"))   or 0.0
        eps_est_val = _to_float(e0.get("estimate")) or 0.0
        eps_diff_pct = safe_pct(eps_actual, eps_est_val)
    
        # 売上（実績・予想） ※あればここが一番素直
        ra = e0.get("revenue") or e0.get("revenueActual") or e0.get("sales")
        re = e0.get("revenueEstimate") or e0.get("salesEstimate")
        if ra is not None:
            f = _to_float(ra)
            if f is not None:
                rev_actual_B = f / 1e9
        if re is not None:
            f = _to_float(re)
            if f is not None:
                rev_est_B = f / 1e9
    
    # 2) 基本メトリクス
    bf = finnhub_client.company_basic_financials(ticker, "all")
    metrics = bf["metric"] if isinstance(bf, dict) and "metric" in bf else {}
    shares_outstanding = get_shares_outstanding(metrics, ticker)
    
    # 3) 売上実績がまだ 0 → financials_reported でフォールバック
    if rev_actual_B == 0.0:
        fin = finnhub_client.financials_reported(symbol=ticker, freq="quarterly")
        report_data = fin.get("data", []) if isinstance(fin, dict) else (fin if isinstance(fin, list) else [])
        if report_data and isinstance(report_data[0], dict):
            ic_obj = (report_data[0].get("report") or {}).get("ic") or report_data[0].get("ic")
            val = extract_ic_number(ic_obj)
            if val is not None:
                rev_actual_B = val / 1e9
    
    # 4) 売上予想がまだ 0 → RPS×発行株数などで補完
    if rev_est_B == 0.0:
        rps_candidates = [
            metrics.get("revenuePerShareForecast"),
            metrics.get("revenuePerShare"),
            metrics.get("revenuePerShareTTM"),
        ]
        rev_total = metrics.get("revenueTTM") or metrics.get("revenueAnnual")
        if rev_total and shares_outstanding:
            f_total = _to_float(rev_total)
            if f_total and shares_outstanding:
                try:
                    rps_candidates.append(f_total / float(shares_outstanding))
                except Exception:
                    pass
    
        rps_used = next((x for x in rps_candidates if isinstance(x, (int, float)) and x > 0), None)
        if rps_used and shares_outstanding:
            rev_est_B = (float(rps_used) * float(shares_outstanding)) / 1e9
    
    # 5) 次期予想
    next_eps_est = (
        metrics.get("nextEarningsPerShare")
        or metrics.get("epsNextQuarter")
        or metrics.get("epsEstimateNextQuarter")
        or "TBD"
    )
    rps_next = metrics.get("revenuePerShareForecast")
    if rps_next and shares_outstanding:
        f_next = _to_float(rps_next)
        if f_next:
            next_rev_B = (f_next * float(shares_outstanding)) / 1e9
    
    # 6) 乖離率・年間
    rev_diff_pct      = safe_pct(rev_actual_B, rev_est_B)
    next_rev_diff_pct = safe_pct(next_rev_B, rev_actual_B) if rev_actual_B else 0.0
    
    annual_eps = (
        metrics.get("epsInclExtraItemsAnnual")
        or metrics.get("epsInclExtraItemsTTM")
        or "TBD"
    )
    rps_ttm = _to_float(metrics.get("revenuePerShareTTM"))
    if rps_ttm and shares_outstanding:
        annual_rev_B = round((rps_ttm * float(shares_outstanding)) / 1e9, 2)

except Exception as e:
    if DEBUG:
        st.error(traceback.format_exc())  # 開発中は詳細表示
    else:
        st.warning("⚠️ 決算データの取得でエラーが発生しました。")
        
# 🎯 ターゲット価格データ（共有で使う）
price_data = pd.DataFrame({
    "Label": ["Before", "After", "Analyst Target", "AI Target"],
    "Price": [181.75, 176.36, 167.24, 178.20]
})

# =============================
# 🎨 ダークカードUI（画像の雰囲気に寄せる）
# 既存の指標変数(eps_actual, eps_est, rev_actual_B, next_rev_B など)をそのまま利用
# =============================

# --- 1) CSS（角丸・影・ダークテーマ） ---
st.markdown("""
<style>
:root{
  --bg:#0e1117; --card:#1a1f2e; --soft:#22293a; --text:#e6e6ea; --muted:#a7b0c0;
  --good:#28d17c; --warn:#f5a524; --bad:#ff4d4f; --chip:#2b3246; --line:#33405c;
}
.block-container{padding-top:1.0rem;}
.card{background:var(--card); border:1px solid #2a3246; border-radius:18px; padding:16px 18px;
      box-shadow:0 8px 30px rgba(0,0,0,.25); color:var(--text); }
.card h3, .card h4, .card h5{margin:0 0 .3rem 0;}
.kv{display:flex; gap:14px; flex-wrap:wrap; margin:.25rem 0 .6rem;}
.kv .chip{background:var(--chip); border:1px solid #38425f; color:var(--muted);
          padding:6px 10px; border-radius:999px; font-size:.82rem;}
.grid{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
.pill{display:flex; align-items:center; gap:12px; background:var(--soft); border:1px solid #2d3650;
     border-radius:16px; padding:14px;}
.pill .dot{width:36px; height:36px; border-radius:50%; display:flex; align-items:center; justify-content:center;
           font-weight:700; color:#0b0e14;}
.pill .lhs{flex:1;}
.pill .lhs .title{color:var(--muted); font-size:.85rem; margin-bottom:2px;}
.pill .lhs .est{color:var(--muted); font-size:.78rem;}
.delta{font-size:.85rem; font-weight:600;}

.tenet-h1 {
  font-family: var(--tenet-head, "Bebas Neue","Oswald","Anton","Arya",sans-serif);
  font-size: 1.8rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  font-weight: 600;
}

.tenet-h2 {
  font-family: var(--tenet-ui, "Oswald","Arya",sans-serif);
  font-size: 1.0rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}

.good{color:var(--good);} .bad{color:var(--bad);} .muted{color:var(--muted);}
.header{display:flex; gap:14px; align-items:center;}
.logo{width:42px; height:42px; border-radius:10px; background:#0b0e14; display:flex; align-items:center; justify-content:center;}
.title-wrap{display:flex; flex-direction:column}
.title-top{font-size:1.1rem; font-weight:700;}
.subtitle{font-size:.9rem; color:var(--muted);}
.section-title{margin:.6rem 0 .3rem; color:var(--muted); font-weight:600; letter-spacing:.02em;}

#追記
.divider-card {
  height:22px;
  background:var(--card);
  border:1px solid #2a3246;
  border-radius:14px;
  margin-top:8px;
  box-shadow:0 6px 20px rgba(0,0,0,.25);
}
.card + .divider-card { margin-bottom:14px; }
#追記終了
</style>
""", unsafe_allow_html=True)

# --- 2) ヘッダー（銘柄名・ティッカー・クォーター） ---
company = yf.Ticker(ticker).info.get("shortName", ticker)
quarter_label = f"${ticker} Q2 2026"  # 必要に応じて動的に
market_cap = yf.Ticker(ticker).info.get("marketCap", None)
def human(n):  # 時価総額の簡易整形
    try:
        if n is None: return "N/A"
        for unit in ["","K","M","B","T","Q"]:
            if abs(n) < 1000.0: return f"{n:,.2f}{unit}"
            n/=1000.0
    except: return "N/A"

pe = yf.Ticker(ticker).info.get("trailingPE", None)
fpe = yf.Ticker(ticker).info.get("forwardPE", None)
peg = yf.Ticker(ticker).info.get("pegRatio", None)

st.markdown(f"""
<div class="card">
  <div class="header">
    <div class="logo">🟢</div>
    <div class="title-wrap">
      <div class="title-top">{company}</div>
      <div class="subtitle">{quarter_label}</div>
    </div>
  </div>
  <div class="kv">
    <span class="chip">Market Cap: <b>{human(market_cap)}</b></span>
    <span class="chip">P/E: <b>{f"{pe:.2f}" if isinstance(pe,(int,float)) else "N/A"}</b></span>
    <span class="chip">Forward P/E: <b>{f"{fpe:.2f}" if isinstance(fpe,(int,float)) else "N/A"}</b></span>
    <span class="chip">PEG: <b>{f"{peg:.2f}" if isinstance(peg,(int,float)) else "N/A"}</b></span>
  </div>
""", unsafe_allow_html=True)
#追記
st.markdown('<div class="divider-card"></div>', unsafe_allow_html=True)

# --- 3) ピル型メトリクス（左：EPS系 / 右：Revenue系） ---
def pill_html(label, value, est=None, delta=None, good=True):
    color = "var(--good)" if good else "var(--bad)"
    dot_bg = "#28d17c" if good else "#ff4d4f"
    delta_html = f'<span class="delta {"good" if good else "bad"}">{delta}</span>' if delta else '<span class="delta muted">N/A</span>'
    est_html = f'<div class="est">Est. {est}</div>' if est is not None else ""
    return f"""
    <div class="pill">
      <div class="dot" style="background:{dot_bg}">{value}</div>
      <div class="lhs">
        <div class="title">{label}</div>
        {est_html}
      </div>
      {delta_html}
    </div>
    """

eps_est = f"{eps_est_val}" if eps_est_val else "N/A"
rev_est_B_disp = f"{rev_est_B:.2f}B" if rev_est_B else "N/A"
next_eps_est_disp = f"{next_eps_est}" if next_eps_est!="TBD" else "TBD"
next_rev_est_disp = f"{next_rev_B:.0f}B" if next_rev_B else "N/A"

grid_html = f"""
  <div class="grid">
    {pill_html("EPS", f"{eps_actual:.2f}" if isinstance(eps_actual,(int,float)) else "TBD",
               est=f"{eps_est}", delta=f"{eps_diff_pct:+.2f}%", good=(eps_diff_pct>=0))}
    {pill_html("Revenue", f"{rev_actual_B:.2f}B", est=f"{rev_est_B_disp}",
               delta=f"{rev_diff_pct:+.2f}%", good=(rev_diff_pct>=0))}
    {pill_html("Next Qtr EPS", f"{next_eps_est_disp}", est="1.19", delta=None, good=True)}
    {pill_html("Next Qtr Rev", f"{next_rev_est_disp}", est="52.76B",
               delta=f"{next_rev_diff_pct:+.2f}%", good=(next_rev_diff_pct>=0))}
  </div>
"""
st.markdown(grid_html, unsafe_allow_html=True)

# --- 4) 横棒ターゲット（Before/After/Analyst/AI） ---
# 既存price_dataを活用し、見た目を調整
min_x = min(price_data["Price"]) - 15
max_x = max(price_data["Price"]) + 40

fig_ui = px.bar(
    price_data, x="Price", y="Label", orientation="h", text=price_data["Price"].map(lambda v: f"${v:,.2f}"),
    color="Label",
    color_discrete_map={
        "Before":"#7bb1ff", "After":"#2fb27a", "Analyst Target":"#f5a524", "AI Target":"#ff6161"
    }
)
fig_ui.update_traces(textposition="inside", insidetextanchor="middle")
# 注釈ライン：$90 と $200（例）
fig_ui.add_shape(type="line", x0=90, x1=90, y0=-0.5, y1=3.5, line=dict(dash="dot", width=1, color="#d6a000"))
fig_ui.add_annotation(x=90, y=3.35, text="$90", showarrow=False, font=dict(size=11, color="#d6a000"))
fig_ui.add_shape(type="line", x0=200, x1=200, y0=-0.5, y1=3.5, line=dict(dash="dot", width=1, color="#ffae00"))
fig_ui.add_annotation(x=200, y=3.35, text="$200", showarrow=False, font=dict(size=11, color="#ffae00"))

# 右端に%差の注釈（After/AIのみ例示）
before = float(price_data.loc[price_data["Label"]=="Before","Price"])
after  = float(price_data.loc[price_data["Label"]=="After","Price"])
ai     = float(price_data.loc[price_data["Label"]=="AI Target","Price"])
fig_ui.add_annotation(x=after, y=1, text=f"{(after-before)/before*100:+.2f}%", showarrow=False, xshift=28, font=dict(size=11, color="#2fb27a"))
fig_ui.add_annotation(x=ai, y=3, text=f"{(ai-before)/before*100:+.2f}%",   showarrow=False, xshift=28, font=dict(size=11, color="#ff6161"))

fig_ui.update_layout(
    title="Stock & Target Prices",
    xaxis_title="", yaxis_title="",
    xaxis=dict(range=[min_x, max_x], gridcolor="#22304b", zeroline=False),
    yaxis=dict(showgrid=False),
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", height=370,
    margin=dict(l=10, r=10, t=50, b=20),
)
st.plotly_chart(fig_ui, use_container_width=True)

# --- 5) AI Rating 行 ---
st.markdown("""
<div class="section-title">AI Rating:</div>
<div class="card" style="display:flex; align-items:center; gap:10px; justify-content:flex-start;">
  <div>📊</div><div class="muted">Coming soon</div>
</div>
<p class="muted" style="margin-top:.4rem;">
  <em>*Earnings report released on 2025-08-27. Informational purposes only. Consult with a professional and conduct sufficient research before making investment decisions.*</em>
</p>
</div>  <!-- 最初の .card を閉じる -->
""", unsafe_allow_html=True)


# ------------------------------------------
# 🤖 AI Rating（仮置き）
# ------------------------------------------
st.markdown("### 🤖 AI Rating: 📈")
st.caption("*Earnings report released on 2025-08-27. Informational purposes only. Please consult with a professional before investing.*")
