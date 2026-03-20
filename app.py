# =============================================================================
# app.py — Crypto Intelligence Dashboard (Streamlit)
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import time
from datetime import datetime

import config
import database as db
import data_collector as dc
import indicators as ind
import scoring as sc
import ai_agent as agent_module

# ─────────────────────────────────────────────────────────────────────────────
# Configuração inicial
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)
db.init_db()

# ─────────────────────────────────────────────────────────────────────────────
# CSS — Dark Terminal Theme
# ─────────────────────────────────────────────────────────────────────────────
st.html("""<link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  /* ── Base ── */
  html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
  .stApp { background: #070b14; color: #c9d4e8; }
  .main .block-container { padding: 1.5rem 2rem; max-width: 1400px; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: #0a0f1e;
    border-right: 1px solid #1a2744;
  }
  [data-testid="stSidebar"] * { color: #c9d4e8 !important; }

  /* ── Tabs ── */
  .stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: transparent;
    border-bottom: 1px solid #1a2744;
    padding-bottom: 0;
  }
  .stTabs [data-baseweb="tab"] {
    height: 44px;
    padding: 0 20px;
    background: #0d1526;
    border: 1px solid #1a2744;
    border-radius: 8px 8px 0 0;
    color: #7a92b8 !important;
    font-family: 'Outfit', sans-serif;
    font-weight: 500;
    font-size: 14px;
    border-bottom: none;
  }
  .stTabs [aria-selected="true"] {
    background: #111d35 !important;
    border-color: #2a4070 !important;
    color: #60a5fa !important;
    border-bottom: 2px solid #3b82f6 !important;
  }

  /* ── Cards ── */
  .kpi-card {
    background: #0d1526;
    border: 1px solid #1a2744;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 12px;
  }
  .kpi-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #4a6080;
    margin-bottom: 4px;
  }
  .kpi-value {
    font-family: 'Space Mono', monospace;
    font-size: 26px;
    font-weight: 700;
    color: #e2e8f0;
    line-height: 1.1;
  }
  .kpi-sub {
    font-size: 12px;
    color: #4a6080;
    margin-top: 4px;
  }

  /* ── Score badge ── */
  .score-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-family: 'Space Mono', monospace;
    font-size: 13px;
    font-weight: 700;
  }

  /* ── OCO card ── */
  .oco-card {
    background: #0d1526;
    border: 1px solid #1a2744;
    border-radius: 12px;
    padding: 20px 24px;
  }
  .oco-title {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #4a6080;
    margin-bottom: 14px;
  }
  .oco-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #141e30;
  }
  .oco-row:last-child { border-bottom: none; }
  .oco-key { font-size: 12px; color: #6b7f9e; }
  .oco-val {
    font-family: 'Space Mono', monospace;
    font-size: 14px;
    font-weight: 700;
    color: #e2e8f0;
  }

  /* ── Buttons ── */
  .stButton > button {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    color: white !important;
    border: none;
    border-radius: 8px;
    font-family: 'Outfit', sans-serif;
    font-weight: 600;
    font-size: 14px;
    padding: 10px 20px;
    width: 100%;
    transition: all 0.2s;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 20px rgba(59,130,246,0.4);
  }

  /* ── Dataframe ── */
  .dataframe { background: #0d1526 !important; }
  [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

  /* ── Inputs e selects ── */
  .stSelectbox > div, .stMultiSelect > div {
    background: #0d1526 !important;
    border-color: #1a2744 !important;
  }

  /* ── Divider ── */
  hr { border-color: #1a2744 !important; }

  /* ── Metric ── */
  [data-testid="metric-container"] {
    background: #0d1526;
    border: 1px solid #1a2744;
    border-radius: 10px;
    padding: 14px 18px;
  }
  [data-testid="metric-container"] label {
    color: #4a6080 !important;
    font-size: 11px !important;
    letter-spacing: 1px;
    text-transform: uppercase;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Space Mono', monospace;
    font-size: 22px !important;
    color: #e2e8f0 !important;
  }

  /* ── Status bar ── */
  .status-bar {
    background: #0d1526;
    border: 1px solid #1a2744;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 12px;
    color: #4a6080;
    font-family: 'Space Mono', monospace;
  }

  /* ── Section header ── */
  .section-header {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #3b82f6;
    margin: 20px 0 12px 0;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, #1a2744, transparent);
  }

  /* ── Plotly charts ── */
  .js-plotly-plot { border-radius: 10px; }
</style>
""")

# ─────────────────────────────────────────────────────────────────────────────
# Helpers de formatação
# ─────────────────────────────────────────────────────────────────────────────

def fmt_price(p: float) -> str:
    if p is None: return "—"
    if p >= 1000:  return f"${p:,.2f}"
    if p >= 1:     return f"${p:.4f}"
    return f"${p:.6f}"

def fmt_pct(p: float) -> str:
    if p is None: return "—"
    arrow = "▲" if p >= 0 else "▼"
    color = "#00d4a1" if p >= 0 else "#ff4444"
    return f'<span style="color:{color};font-family:Space Mono,monospace">{arrow} {abs(p):.2f}%</span>'

def fmt_large(n: float) -> str:
    if n is None: return "—"
    if n >= 1e12: return f"${n/1e12:.2f}T"
    if n >= 1e9:  return f"${n/1e9:.2f}B"
    if n >= 1e6:  return f"${n/1e6:.2f}M"
    return f"${n:,.0f}"

def score_color(score: float) -> str:
    if score >= 85: return "#00ffcc"
    if score >= 70: return "#00d4a1"
    if score >= 55: return "#3b82f6"
    if score >= 40: return "#f59e0b"
    return "#ff4444"


# ─────────────────────────────────────────────────────────────────────────────
# Session State
# ─────────────────────────────────────────────────────────────────────────────
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = []
if "last_run" not in st.session_state:
    st.session_state.last_run = None
if "fear_greed" not in st.session_state:
    st.session_state.fear_greed = {"value": 50, "label": "Neutral"}
if "global_market" not in st.session_state:
    st.session_state.global_market = {}
if "crypto_agent" not in st.session_state:
    st.session_state.crypto_agent = agent_module.CryptoAgent()
if "agent_report" not in st.session_state:
    st.session_state.agent_report = ""
if "agent_chat" not in st.session_state:
    st.session_state.agent_chat = []


# ─────────────────────────────────────────────────────────────────────────────
# Cache de dados
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def cached_ohlcv(symbol, timeframe):
    return dc.fetch_ohlcv(symbol, timeframe)

@st.cache_data(ttl=3600)
def cached_fear_greed():
    return dc.fetch_fear_greed()

@st.cache_data(ttl=3600)
def cached_global_market():
    return dc.fetch_global_market()

@st.cache_data(ttl=60)
def cached_ticker(symbol):
    return dc.fetch_ticker(symbol)


# ─────────────────────────────────────────────────────────────────────────────
# Lógica de análise completa
# ─────────────────────────────────────────────────────────────────────────────
def run_full_analysis(watchlist: list, primary_tf: str) -> list:
    """Roda análise completa para todos os ativos da watchlist."""
    fg    = dc.fetch_fear_greed()
    gm    = dc.fetch_global_market()
    st.session_state.fear_greed   = fg
    st.session_state.global_market = gm
    db.save_fear_greed(fg["value"], fg["label"], fg.get("timestamp", ""))

    results = []
    bar     = st.progress(0, text="Iniciando análise...")

    for i, symbol in enumerate(watchlist):
        bar.progress((i + 1) / len(watchlist), text=f"Analisando {symbol}...")

        try:
            # Coleta dados
            all_data = dc.collect_all(symbol)
            tf_ohlcv = all_data["ohlcv"]

            if primary_tf not in tf_ohlcv or tf_ohlcv[primary_tf].empty:
                continue

            df_primary = ind.compute_indicators(tf_ohlcv[primary_tf])
            last       = ind.get_last_values(df_primary)
            price      = last.get("close") or all_data["ticker"].get("price", 0)

            # Score
            result = sc.compute_score(
                df_primary    = df_primary,
                tf_ohlcv      = tf_ohlcv,
                fear_greed    = fg["value"],
                funding_rate  = all_data.get("funding_rate"),
            )

            # OCO
            oco = ind.calc_oco_params(df_primary, price)
            sr  = ind.calc_support_resistance(df_primary)
            div = ind.detect_rsi_divergence(df_primary)

            row = {
                "symbol":        symbol,
                "price":         price,
                "score":         result["total"],
                "score_label":   result["label"],
                "score_color":   result["color"],
                "sub_scores":    result["sub_scores"],
                "tf_signals":    result["tf_signals"],
                "divergence":    div,
                "oco":           oco,
                "support_resistance": sr,
                "indicators":    {k: v for k, v in last.items() if isinstance(v, (int, float)) and v is not None},
                "price_changes": all_data.get("price_changes", {}),
                "funding_rate":  all_data.get("funding_rate"),
                "open_interest": all_data.get("open_interest"),
                "ticker":        all_data.get("ticker", {}),
            }
            results.append(row)

            # Persiste no banco
            db.save_analysis(
                symbol    = symbol,
                timeframe = primary_tf,
                score     = result["total"],
                indicators= {k: v for k, v in last.items() if isinstance(v, (int, float))},
                oco_params= oco,
                price     = price,
            )
        except Exception as e:
            st.warning(f"⚠ Erro ao analisar {symbol}: {e}")

    bar.empty()
    results.sort(key=lambda x: x["score"], reverse=True)

    # Salva snapshot top-10
    if results:
        top10 = [{"symbol": r["symbol"], "score": r["score"], "price": r["price"]}
                 for r in results[:10]]
        db.save_snapshot(top10)

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Plotly — Gráfico de candles + indicadores
# ─────────────────────────────────────────────────────────────────────────────
def build_main_chart(df: pd.DataFrame, symbol: str, show_bb: bool = True) -> go.Figure:
    """Gráfico de candlestick com EMAs, BBands e volume."""
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.72, 0.28],
        shared_xaxes=True,
        vertical_spacing=0.02,
    )

    # Candles
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name="OHLC",
        increasing_line_color="#00d4a1", increasing_fillcolor="#00d4a1",
        decreasing_line_color="#ff4444", decreasing_fillcolor="#ff4444",
    ), row=1, col=1)

    # BBands
    if show_bb and "BB_UPPER" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_UPPER"], name="BB Superior",
            line=dict(color="rgba(100,150,255,0.4)", width=1, dash="dot"),
            showlegend=False,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_LOWER"], name="BB Inferior",
            line=dict(color="rgba(100,150,255,0.4)", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(59,130,246,0.05)",
            showlegend=False,
        ), row=1, col=1)

    # EMAs
    ema_colors = {9: "#f59e0b", 21: "#a78bfa", 50: "#60a5fa", 200: "#f472b6"}
    for period, color in ema_colors.items():
        col_name = f"EMA{period}"
        if col_name in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col_name], name=f"EMA{period}",
                line=dict(color=color, width=1.2),
            ), row=1, col=1)

    # VWAP
    if "VWAP" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["VWAP"], name="VWAP",
            line=dict(color="rgba(255,165,0,0.6)", width=1, dash="dash"),
        ), row=1, col=1)

    # Volume
    colors = ["#00d4a1" if c else "#ff4444" for c in df["close"] >= df["open"]]
    fig.add_trace(go.Bar(
        x=df.index, y=df["volume"], name="Volume",
        marker_color=colors, opacity=0.7,
        showlegend=False,
    ), row=2, col=1)
    if "VOL_SMA" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["VOL_SMA"], name="Vol SMA",
            line=dict(color="#f59e0b", width=1),
        ), row=2, col=1)

    fig.update_layout(
        title=dict(text=f"<b>{symbol}</b>", font=dict(size=16, color="#e2e8f0")),
        paper_bgcolor="#070b14",
        plot_bgcolor="#0d1526",
        font=dict(color="#7a92b8", family="Outfit"),
        xaxis_rangeslider_visible=False,
        height=480,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    for axis in ["xaxis", "yaxis", "xaxis2", "yaxis2"]:
        fig.update_layout(**{axis: dict(
            gridcolor="#111d35", zerolinecolor="#1a2744",
            tickfont=dict(size=10, color="#4a6080"),
        )})
    return fig


def build_indicators_chart(df: pd.DataFrame, indicator: str = "RSI") -> go.Figure:
    """Gráfico de indicador inferior (RSI, MACD, StochRSI, ADX)."""
    fig = go.Figure()
    bg  = "#0d1526"

    if indicator == "RSI" and "RSI" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI"], name="RSI",
            line=dict(color="#60a5fa", width=2), fill="tozeroy",
            fillcolor="rgba(59,130,246,0.08)",
        ))
        for level, color, name in [(70, "#ff4444", "Sobrecomprado"), (30, "#00d4a1", "Sobrevendido")]:
            fig.add_hline(y=level, line_dash="dot", line_color=color, opacity=0.5,
                         annotation_text=name, annotation_font_size=10)
        fig.add_hline(y=50, line_dash="dot", line_color="#4a6080", opacity=0.4)

    elif indicator == "MACD" and "MACD" in df.columns:
        fig.add_trace(go.Bar(
            x=df.index, y=df["MACD_HIST"], name="Histograma",
            marker_color=["#00d4a1" if v >= 0 else "#ff4444" for v in df["MACD_HIST"].fillna(0)],
        ))
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
            line=dict(color="#60a5fa", width=1.5)))
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_SIGNAL"], name="Signal",
            line=dict(color="#f59e0b", width=1.5, dash="dot")))

    elif indicator == "StochRSI" and "STOCHRSI_K" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["STOCHRSI_K"], name="%K",
            line=dict(color="#60a5fa", width=1.5)))
        fig.add_trace(go.Scatter(x=df.index, y=df["STOCHRSI_D"], name="%D",
            line=dict(color="#f59e0b", width=1.5, dash="dot")))
        for level, color in [(80, "#ff4444"), (20, "#00d4a1")]:
            fig.add_hline(y=level, line_dash="dot", line_color=color, opacity=0.4)

    elif indicator == "ADX" and "ADX" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["ADX"], name="ADX",
            line=dict(color="#f59e0b", width=2)))
        if "ADX_POS" in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df["ADX_POS"], name="+DI",
                line=dict(color="#00d4a1", width=1.2, dash="dot")))
            fig.add_trace(go.Scatter(x=df.index, y=df["ADX_NEG"], name="-DI",
                line=dict(color="#ff4444", width=1.2, dash="dot")))
        fig.add_hline(y=25, line_dash="dot", line_color="#4a6080", opacity=0.5,
                     annotation_text="Tendência forte", annotation_font_size=10)

    fig.update_layout(
        paper_bgcolor="#070b14", plot_bgcolor=bg,
        font=dict(color="#7a92b8", family="Outfit"),
        height=200, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11), orientation="h"),
        xaxis=dict(gridcolor="#111d35", tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#111d35", tickfont=dict(size=10)),
    )
    return fig


def build_score_radar(sub_scores: dict) -> go.Figure:
    """Radar chart dos sub-scores."""
    categories = list(sub_scores.keys())
    labels_pt  = {
        "rsi": "RSI", "macd": "MACD", "ema_trend": "EMAs",
        "bb_position": "BBands", "stoch_rsi": "StochRSI",
        "adx": "ADX", "volume": "Volume", "obv_trend": "OBV",
        "multi_tf": "Multi-TF", "fear_greed": "Fear&Greed",
        "funding_rate": "Funding",
    }
    labels     = [labels_pt.get(c, c) for c in categories]
    scores     = [sub_scores[c]["raw"] for c in categories]

    fig = go.Figure(go.Scatterpolar(
        r=scores, theta=labels, fill="toself",
        fillcolor="rgba(59,130,246,0.15)",
        line=dict(color="#3b82f6", width=2),
        marker=dict(color="#60a5fa", size=5),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#0d1526",
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9),
                          gridcolor="#1a2744", color="#4a6080"),
            angularaxis=dict(tickfont=dict(size=11, color="#c9d4e8"), gridcolor="#1a2744"),
        ),
        paper_bgcolor="#070b14",
        font=dict(color="#c9d4e8", family="Outfit"),
        height=320,
        margin=dict(l=40, r=40, t=20, b=20),
        showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-family:Space Mono,monospace;font-size:18px;font-weight:700;color:#60a5fa;margin-bottom:4px">⚡ CRYPTO INTEL</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:11px;color:#4a6080;letter-spacing:1px;margin-bottom:20px">DASHBOARD DE ANÁLISE TÉCNICA</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:10px;color:#4a6080;letter-spacing:1px;margin-bottom:30px;margin-top:-20px">Powered by raonigs/div>', unsafe_allow_html=True)
    st.divider()

    # ── Seletor de Modelo de IA ──────────────────────────────────────────────
    st.markdown("**🤖 Modelo de IA**")

    key_status    = agent_module.get_key_status()
    all_providers = list(config.AI_MODELS_CATALOG.keys())
    providers_with_key    = [p for p in all_providers if key_status.get(p)]
    providers_without_key = [p for p in all_providers if not key_status.get(p)]

    if not providers_with_key:
        st.warning("Nenhuma API key encontrada no `.env`")
        provider_options_display = all_providers
    else:
        provider_options_display = providers_with_key + [f"{p}  🔒" for p in providers_without_key]

    selected_provider_raw = st.selectbox(
        "Provedor", provider_options_display,
        label_visibility="collapsed", key="sidebar_provider",
    )
    selected_provider = selected_provider_raw.replace("  🔒", "")
    prov_info = config.AI_MODELS_CATALOG.get(selected_provider, {})
    has_key   = key_status.get(selected_provider, False)

    if prov_info:
        model_options        = list(prov_info.get("models", {}).keys())
        selected_model_label = st.selectbox(
            "Modelo", model_options,
            label_visibility="collapsed", key="sidebar_model",
            disabled=not has_key,
        )
        selected_model_id = prov_info["models"].get(selected_model_label, config.AI_DEFAULT_MODEL)

        if has_key:
            st.markdown('<div style="display:flex;align-items:center;gap:6px;margin:4px 0 8px 0"><div style="width:7px;height:7px;border-radius:50%;background:#00d4a1"></div><span style="font-size:11px;color:#00d4a1">Key configurada ✓</span></div>', unsafe_allow_html=True)
        else:
            env_key = prov_info.get("env_key","").upper()
            st.markdown(f'<div style="font-size:11px;color:#ff4444;margin:4px 0 8px 0">🔒 Adicione {env_key}_API_KEY no .env</div>', unsafe_allow_html=True)

        if "crypto_agent" in st.session_state and has_key:
            if selected_model_id != st.session_state.crypto_agent.model:
                st.session_state.crypto_agent.set_model(selected_model_id)

    st.divider()

    # ── Watchlist ────────────────────────────────────────────────────────────
    st.markdown("**📋 Watchlist**")
    selected_coins = st.multiselect(
        "Selecionar moedas", options=config.WATCHLIST,
        default=config.WATCHLIST[:12], label_visibility="collapsed",
    )

    st.markdown("**⏱ Timeframe Principal**")
    primary_tf = st.selectbox(
        "Timeframe", ["4h", "1h", "1d"], label_visibility="collapsed",
    )

    st.divider()
    run_btn = st.button("▶  RODAR ANÁLISE COMPLETA", type="primary")
    st.divider()

    if st.session_state.last_run:
        st.markdown(f'<div class="status-bar">✓ Última análise:<br>{st.session_state.last_run}</div>', unsafe_allow_html=True)

    fg       = st.session_state.fear_greed
    fg_val   = fg.get("value", 50)
    fg_label = fg.get("label", "Neutral")
    fg_color = "#ff4444" if fg_val < 25 else "#f59e0b" if fg_val < 45 else "#4a6080" if fg_val < 55 else "#60a5fa" if fg_val < 75 else "#ff4444"
    st.markdown(f'''
    <div class="kpi-card" style="margin-top:16px">
      <div class="kpi-label">Fear & Greed Index</div>
      <div class="kpi-value" style="color:{fg_color}">{fg_val}</div>
      <div class="kpi-sub">{fg_label}</div>
    </div>''', unsafe_allow_html=True)

    gm = st.session_state.global_market
    if gm:
        btc_dom = gm.get("btc_dominance", "—")
        eth_dom = gm.get("eth_dominance", "—")
        st.markdown(f'''
        <div class="kpi-card">
          <div class="kpi-label">Dominância</div>
          <div style="font-family:Space Mono,monospace;font-size:14px;color:#f59e0b">BTC {btc_dom}%</div>
          <div style="font-family:Space Mono,monospace;font-size:14px;color:#a78bfa">ETH {eth_dom}%</div>
        </div>''', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Execução da análise
# ─────────────────────────────────────────────────────────────────────────────
if run_btn and selected_coins:
    with st.spinner("Coletando dados e calculando indicadores..."):
        st.session_state.analysis_results = run_full_analysis(selected_coins, primary_tf)
        st.session_state.last_run = datetime.now().strftime("%d/%m/%Y %H:%M")
        # Atualiza contexto do agente com os dados frescos
        if st.session_state.analysis_results:
            st.session_state.crypto_agent.update_context(
                top_results   = st.session_state.analysis_results[:10],
                fear_greed    = st.session_state.fear_greed,
                global_market = st.session_state.global_market,
            )
            st.session_state.agent_report = ""  # reseta relatório para gerar novo
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="display:flex;align-items:baseline;gap:16px;margin-bottom:4px">
  <div style="font-family:Space Mono,monospace;font-size:22px;font-weight:700;color:#e2e8f0">
    ⚡ Crypto Intelligence Dashboard
  </div>
  <div style="font-size:12px;color:#4a6080;font-family:Space Mono,monospace">
    {datetime.now().strftime('%d/%m/%Y %H:%M')}
  </div>
</div>
<div style="font-size:13px;color:#4a6080;margin-bottom:24px">
  Análise técnica multi-timeframe · Scoring quantitativo · Parâmetros OCO automáticos
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Dashboard",
    "🔍  Análise Detalhada",
    "📋  Parâmetros OCO",
    "📜  Histórico",
    "🤖  Agente IA",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Dashboard
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    results = st.session_state.analysis_results
    gm      = st.session_state.global_market

    if not results:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;color:#4a6080">
          <div style="font-size:48px;margin-bottom:16px">⚡</div>
          <div style="font-size:18px;font-weight:600;color:#7a92b8;margin-bottom:8px">
            Nenhuma análise executada
          </div>
          <div style="font-size:13px">
            Selecione as moedas na sidebar e clique em <strong style="color:#60a5fa">▶ RODAR ANÁLISE COMPLETA</strong>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # KPI cards
        c1, c2, c3, c4 = st.columns(4)
        fg  = st.session_state.fear_greed

        with c1:
            fg_color = "#ff4444" if fg["value"] < 30 else "#f59e0b" if fg["value"] < 50 else "#60a5fa" if fg["value"] < 70 else "#ff6644"
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">Fear & Greed</div>
              <div class="kpi-value" style="color:{fg_color}">{fg["value"]}</div>
              <div class="kpi-sub">{fg["label"]}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            btc = gm.get("btc_dominance", "—")
            mkt_chg = gm.get("market_cap_change", 0)
            chg_col = "#00d4a1" if mkt_chg >= 0 else "#ff4444"
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">BTC Dominância</div>
              <div class="kpi-value">{btc}%</div>
              <div class="kpi-sub" style="color:{chg_col}">Mercado: {mkt_chg:+.2f}% 24h</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            mc = fmt_large(gm.get("total_market_cap"))
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">Market Cap Total</div>
              <div class="kpi-value" style="font-size:20px">{mc}</div>
              <div class="kpi-sub">Todas as criptomoedas</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            top_score = max(r["score"] for r in results) if results else 0
            top_sym   = next((r["symbol"] for r in results if r["score"] == top_score), "—")
            sc_col    = score_color(top_score)
            st.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-label">Top Score</div>
              <div class="kpi-value" style="color:{sc_col}">{top_score:.1f}</div>
              <div class="kpi-sub">{top_sym.replace("/USDT","")}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header">🏆 Ranking por Score</div>', unsafe_allow_html=True)

        # Tabela principal
        table_rows = []
        for r in results:
            pc = r.get("price_changes", {})
            ind_vals = r.get("indicators", {})
            rsi  = ind_vals.get("RSI")
            macd_bull = (r["sub_scores"].get("macd", {}).get("raw", 50) or 50) > 60
            fund = r.get("funding_rate")

            table_rows.append({
                "Ativo":       r["symbol"].replace("/USDT", ""),
                "Preço":       fmt_price(r["price"]),
                "1h %":        pc.get("change_1h", 0),
                "4h %":        pc.get("change_4h", 0),
                "24h %":       pc.get("change_24h", 0),
                "7d %":        pc.get("change_7d", 0),
                "RSI":         f"{rsi:.1f}" if rsi else "—",
                "Score":       r["score"],
                "Rating":      r["score_label"],
                "Divergência": "🟢 Bull" if r.get("divergence") == "bullish" else ("🔴 Bear" if r.get("divergence") == "bearish" else "—"),
                "Funding":     f"{fund*100:+.3f}%" if fund else "—",
            })

        df_table = pd.DataFrame(table_rows)

        # Coloração do dataframe
        def color_pct(v):
            if isinstance(v, float):
                return "color:#00d4a1" if v >= 0 else "color:#ff4444"
            return ""
        def color_score(v):
            if isinstance(v, float):
                c = score_color(v)
                return f"color:{c};font-weight:700;font-family:Space Mono,monospace"
            return ""

        styled = (
            df_table.style
            .applymap(color_pct, subset=["1h %", "4h %", "24h %", "7d %"])
            .applymap(color_score, subset=["Score"])
            .format({
                "1h %": "{:+.2f}%", "4h %": "{:+.2f}%",
                "24h %": "{:+.2f}%", "7d %": "{:+.2f}%",
                "Score": "{:.1f}",
            })
            .set_properties(**{"background-color": "#0d1526", "color": "#c9d4e8"})
        )
        st.dataframe(styled, use_container_width=True, height=420)

        # Score distribution chart
        st.markdown('<div class="section-header">📊 Distribuição de Scores</div>', unsafe_allow_html=True)
        col_chart1, col_chart2 = st.columns([2, 1])
        with col_chart1:
            symbols = [r["symbol"].replace("/USDT","") for r in results]
            scores  = [r["score"] for r in results]
            colors  = [score_color(s) for s in scores]
            fig_bar = go.Figure(go.Bar(
                x=symbols, y=scores,
                marker_color=colors,
                text=[f"{s:.1f}" for s in scores],
                textposition="outside",
                textfont=dict(size=11, family="Space Mono"),
            ))
            fig_bar.update_layout(
                paper_bgcolor="#070b14", plot_bgcolor="#0d1526",
                font=dict(color="#7a92b8"), height=280,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(gridcolor="#111d35", tickfont=dict(size=11)),
                yaxis=dict(gridcolor="#111d35", range=[0, 105]),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_chart2:
            # Top 5 resumo
            st.markdown("**🥇 Top 5 Picks**")
            for r in results[:5]:
                sym = r["symbol"].replace("/USDT", "")
                sc_val = r["score"]
                sc_col = score_color(sc_val)
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:8px 12px;background:#0d1526;border-radius:8px;margin-bottom:6px;
                    border:1px solid #1a2744">
                  <div style="font-weight:600;color:#e2e8f0">{sym}</div>
                  <div style="font-family:Space Mono,monospace;font-weight:700;
                      color:{sc_col};font-size:16px">{sc_val:.1f}</div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Análise Detalhada
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    results = st.session_state.analysis_results
    symbols = [r["symbol"] for r in results]

    if not results:
        st.info("Execute a análise primeiro (sidebar → ▶ RODAR ANÁLISE COMPLETA)")
    else:
        sel_symbol = st.selectbox("Selecionar ativo", symbols, format_func=lambda x: x.replace("/USDT","") + " / USDT")
        sel_result = next((r for r in results if r["symbol"] == sel_symbol), None)

        if sel_result:
            # Header da coin
            price  = sel_result["price"]
            score  = sel_result["score"]
            sc_col = score_color(score)
            pc     = sel_result.get("price_changes", {})
            fund   = sel_result.get("funding_rate")
            oi     = sel_result.get("open_interest")

            h1, h2, h3, h4, h5 = st.columns(5)
            with h1:
                st.metric("Preço", fmt_price(price))
            with h2:
                st.metric("1h", f"{pc.get('change_1h',0):+.2f}%")
            with h3:
                st.metric("24h", f"{pc.get('change_24h',0):+.2f}%")
            with h4:
                st.metric("7d", f"{pc.get('change_7d',0):+.2f}%")
            with h5:
                st.markdown(f"""
                <div class="kpi-card" style="margin:0">
                  <div class="kpi-label">Score</div>
                  <div class="kpi-value" style="color:{sc_col}">{score:.1f}</div>
                  <div class="kpi-sub">{sel_result["score_label"]}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("")

            # Busca candles para o gráfico
            with st.spinner(f"Carregando gráfico {sel_symbol}..."):
                df_chart = ind.compute_indicators(
                    cached_ohlcv(sel_symbol, primary_tf)
                )

            if not df_chart.empty:
                # Gráfico principal
                show_bb = st.checkbox("Bandas de Bollinger", value=True)
                fig_main = build_main_chart(df_chart, sel_symbol, show_bb)
                st.plotly_chart(fig_main, use_container_width=True)

                # Indicador inferior
                ind_choice = st.selectbox("Indicador inferior", ["RSI", "MACD", "StochRSI", "ADX"])
                fig_ind = build_indicators_chart(df_chart, ind_choice)
                st.plotly_chart(fig_ind, use_container_width=True)

            # Score breakdown
            st.markdown('<div class="section-header">🎯 Breakdown do Score</div>', unsafe_allow_html=True)
            col_radar, col_table = st.columns([1, 1])

            with col_radar:
                if sel_result.get("sub_scores"):
                    fig_radar = build_score_radar(sel_result["sub_scores"])
                    st.plotly_chart(fig_radar, use_container_width=True)

            with col_table:
                sub = sel_result.get("sub_scores", {})
                labels_pt = {
                    "rsi": "RSI", "macd": "MACD", "ema_trend": "Alinhamento EMAs",
                    "bb_position": "Bollinger Bands", "stoch_rsi": "Stochastic RSI",
                    "adx": "ADX / Força", "volume": "Volume Relativo",
                    "obv_trend": "OBV / VWAP", "multi_tf": "Multi-Timeframe",
                    "fear_greed": "Fear & Greed", "funding_rate": "Funding Rate",
                }
                for key, data in sub.items():
                    raw  = data.get("raw", 0)
                    wgt  = data.get("weighted", 0)
                    maxw = data.get("max_weight", 0)
                    lbl  = data.get("label", "")
                    col  = score_color(raw)
                    pct_fill = int(raw)
                    st.markdown(f"""
                    <div style="margin-bottom:10px">
                      <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                        <span style="font-size:12px;color:#c9d4e8">{labels_pt.get(key,key)}</span>
                        <span style="font-family:Space Mono,monospace;font-size:12px;color:{col}">{raw:.0f} / 100</span>
                      </div>
                      <div style="background:#111d35;border-radius:4px;height:6px;overflow:hidden">
                        <div style="width:{pct_fill}%;height:100%;background:{col};border-radius:4px;transition:width 0.3s"></div>
                      </div>
                      <div style="font-size:11px;color:#4a6080;margin-top:2px">{lbl}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Info extra
            extra_col1, extra_col2 = st.columns(2)
            with extra_col1:
                div = sel_result.get("divergence")
                st.markdown(f"""
                <div class="kpi-card">
                  <div class="kpi-label">Divergência RSI</div>
                  <div style="font-size:16px;color:{'#00d4a1' if div=='bullish' else '#ff4444' if div=='bearish' else '#4a6080'}">
                    {'🟢 Divergência Bullish detectada' if div=='bullish' else '🔴 Divergência Bearish detectada' if div=='bearish' else '⬜ Sem divergência'}
                  </div>
                </div>""", unsafe_allow_html=True)
            with extra_col2:
                sr = sel_result.get("support_resistance", {})
                if sr:
                    st.markdown(f"""
                    <div class="kpi-card">
                      <div class="kpi-label">Suporte & Resistência (Pivot)</div>
                      <div style="font-family:Space Mono,monospace;font-size:13px;line-height:1.8">
                        <span style="color:#ff4444">R2:</span> {fmt_price(sr.get('resistance_2'))} &nbsp;
                        <span style="color:#f59e0b">R1:</span> {fmt_price(sr.get('resistance_1'))}<br>
                        <span style="color:#60a5fa">Pivot:</span> {fmt_price(sr.get('pivot'))}<br>
                        <span style="color:#a78bfa">S1:</span> {fmt_price(sr.get('support_1'))} &nbsp;
                        <span style="color:#00d4a1">S2:</span> {fmt_price(sr.get('support_2'))}
                      </div>
                    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Parâmetros OCO
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    results = st.session_state.analysis_results

    if not results:
        st.info("Execute a análise primeiro (sidebar → ▶ RODAR ANÁLISE COMPLETA)")
    else:
        st.markdown("""
        <div style="background:#0d1526;border:1px solid #1a2744;border-radius:10px;padding:14px 18px;margin-bottom:20px;font-size:13px;color:#7a92b8">
          💡 <strong style="color:#60a5fa">Como usar no Binance:</strong>
          Compre o ativo e então crie uma ordem OCO (One-Cancels-Other) em Spot → 
          <em>Stop-Limit</em> com os valores abaixo. O Take Profit é a Limit Price, 
          o Stop Loss é o Stop Price e o Stop Limit é o Limit Price do stop.
        </div>
        """, unsafe_allow_html=True)

        # Filtro
        min_score = st.slider("Score mínimo", 0, 100, 50, key="oco_score_filter")
        filtered  = [r for r in results if r["score"] >= min_score and r.get("oco")]
        filtered.sort(key=lambda x: x["score"], reverse=True)

        if not filtered:
            st.warning("Nenhum ativo com score suficiente ou OCO calculado.")
        else:
            for r in filtered:
                sym   = r["symbol"].replace("/USDT","")
                price = r["price"]
                oco   = r["oco"]
                sc_v  = r["score"]
                sc_c  = score_color(sc_v)

                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:16px;margin:24px 0 10px 0">
                  <div style="font-size:18px;font-weight:700;color:#e2e8f0">{sym} / USDT</div>
                  <div style="font-family:Space Mono,monospace;font-size:13px;color:#7a92b8">{fmt_price(price)}</div>
                  <div style="background:{sc_c}22;border:1px solid {sc_c}44;border-radius:20px;
                      padding:2px 12px;font-family:Space Mono,monospace;font-size:13px;
                      font-weight:700;color:{sc_c}">Score: {sc_v:.1f}</div>
                </div>
                """, unsafe_allow_html=True)

                cols = st.columns(3)
                scenario_colors = {
                    "conservador": ("#f59e0b", "🛡️ Conservador"),
                    "moderado":    ("#60a5fa", "⚖️ Moderado"),
                    "agressivo":   ("#a78bfa", "🚀 Agressivo"),
                }

                for i, (scenario_key, (color, label)) in enumerate(scenario_colors.items()):
                    params = oco.get(scenario_key)
                    if not params:
                        continue
                    with cols[i]:
                        rr     = params["rr_ratio"]
                        tp_pct = params["tp_pct"]
                        sl_pct = params["sl_pct"]
                        st.markdown(f"""
                        <div class="oco-card" style="border-color:{color}33">
                          <div class="oco-title" style="color:{color}">{label}</div>
                          <div class="oco-row">
                            <span class="oco-key">💰 Entry (Compra)</span>
                            <span class="oco-val">{fmt_price(params['entry'])}</span>
                          </div>
                          <div class="oco-row">
                            <span class="oco-key">🎯 Take Profit</span>
                            <span class="oco-val" style="color:#00d4a1">{fmt_price(params['take_profit'])}</span>
                          </div>
                          <div class="oco-row">
                            <span class="oco-key">🛑 Stop Loss</span>
                            <span class="oco-val" style="color:#ff4444">{fmt_price(params['stop_loss'])}</span>
                          </div>
                          <div class="oco-row">
                            <span class="oco-key">📉 Stop Limit</span>
                            <span class="oco-val" style="color:#ff7777">{fmt_price(params['stop_limit'])}</span>
                          </div>
                          <div class="oco-row">
                            <span class="oco-key">ATR ({config.ATR_LENGTH})</span>
                            <span class="oco-val" style="color:#7a92b8">{fmt_price(params['atr'])}</span>
                          </div>
                          <div style="margin-top:12px;padding-top:10px;border-top:1px solid #1a2744;
                              display:flex;justify-content:space-between">
                            <div style="text-align:center">
                              <div style="font-size:10px;color:#4a6080;letter-spacing:1px">LUCRO</div>
                              <div style="font-family:Space Mono,monospace;font-weight:700;color:#00d4a1">+{tp_pct:.2f}%</div>
                            </div>
                            <div style="text-align:center">
                              <div style="font-size:10px;color:#4a6080;letter-spacing:1px">RISCO</div>
                              <div style="font-family:Space Mono,monospace;font-weight:700;color:#ff4444">-{sl_pct:.2f}%</div>
                            </div>
                            <div style="text-align:center">
                              <div style="font-size:10px;color:#4a6080;letter-spacing:1px">R:R</div>
                              <div style="font-family:Space Mono,monospace;font-weight:700;color:{color}">{rr:.2f}</div>
                            </div>
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Histórico
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">📜 Histórico de Análises</div>', unsafe_allow_html=True)

    col_h1, col_h2 = st.columns([1, 2])

    with col_h1:
        hist_symbol = st.selectbox(
            "Ativo",
            options=["Todos"] + [s.replace("/USDT","") for s in config.WATCHLIST],
            key="hist_symbol"
        )
        hist_limit  = st.slider("Registros", 20, 200, 50, key="hist_limit")

    with col_h2:
        sym_query = None if hist_symbol == "Todos" else hist_symbol + "/USDT"
        df_hist   = db.get_history(sym_query, hist_limit)

        if df_hist.empty:
            st.info("Nenhum registro encontrado. Execute a análise para salvar dados.")
        else:
            df_hist["timestamp"] = pd.to_datetime(df_hist["timestamp"])
            df_show = df_hist[["symbol","timestamp","score","price","timeframe"]].copy()
            df_show.columns = ["Ativo","Data/Hora","Score","Preço","Timeframe"]
            st.dataframe(df_show, use_container_width=True, height=280)

    # Gráfico de evolução de score
    if hist_symbol != "Todos":
        sym_full  = hist_symbol + "/USDT"
        df_scores = db.get_score_history(sym_full, 50)
        if not df_scores.empty:
            st.markdown(f'<div class="section-header">📈 Evolução do Score — {hist_symbol}</div>', unsafe_allow_html=True)
            fig_evo = go.Figure()
            fig_evo.add_trace(go.Scatter(
                x=df_scores["timestamp"], y=df_scores["score"],
                name="Score",
                line=dict(color="#3b82f6", width=2),
                fill="tozeroy", fillcolor="rgba(59,130,246,0.08)",
                mode="lines+markers", marker=dict(size=6, color="#60a5fa"),
            ))
            for level, color, dash in [(85, "#00d4a1", "dot"), (55, "#f59e0b", "dot"), (40, "#ff4444", "dot")]:
                fig_evo.add_hline(y=level, line_dash=dash, line_color=color, opacity=0.4)
            fig_evo.update_layout(
                paper_bgcolor="#070b14", plot_bgcolor="#0d1526",
                font=dict(color="#7a92b8"), height=250,
                margin=dict(l=0, r=0, t=10, b=0),
                yaxis=dict(range=[0, 105], gridcolor="#111d35"),
                xaxis=dict(gridcolor="#111d35"),
            )
            st.plotly_chart(fig_evo, use_container_width=True)

    # Snapshots
    st.markdown('<div class="section-header">📷 Snapshots do Top-10</div>', unsafe_allow_html=True)
    snapshots = db.get_snapshots(10)
    if snapshots:
        for snap in snapshots[:5]:
            top10  = snap["top10"]
            dt_str = snap["created_at"]
            top10_str = "  |  ".join([f"{t['symbol'].replace('/USDT','')} {t['score']:.0f}" for t in top10[:5]])
            st.markdown(f"""
            <div class="status-bar" style="margin-bottom:8px">
              <span style="color:#60a5fa">{dt_str}</span> &nbsp;&nbsp; {top10_str}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhum snapshot salvo ainda.")

    # Fear & Greed histórico
    st.markdown('<div class="section-header">😱 Histórico Fear & Greed</div>', unsafe_allow_html=True)
    df_fg = db.get_fear_greed_history(30)
    if not df_fg.empty:
        fig_fg = go.Figure()
        fig_fg.add_trace(go.Scatter(
            x=df_fg["timestamp"], y=df_fg["value"],
            fill="tozeroy", fillcolor="rgba(245,158,11,0.1)",
            line=dict(color="#f59e0b", width=2),
            mode="lines+markers", marker=dict(size=5),
        ))
        fig_fg.add_hline(y=25, line_dash="dot", line_color="#00d4a1", opacity=0.5,
                        annotation_text="Medo Extremo")
        fig_fg.add_hline(y=75, line_dash="dot", line_color="#ff4444", opacity=0.5,
                        annotation_text="Ganância Extrema")
        fig_fg.update_layout(
            paper_bgcolor="#070b14", plot_bgcolor="#0d1526",
            font=dict(color="#7a92b8"), height=200,
            margin=dict(l=0, r=0, t=10, b=0),
            yaxis=dict(range=[0, 100], gridcolor="#111d35"),
            xaxis=dict(gridcolor="#111d35"),
        )
        st.plotly_chart(fig_fg, use_container_width=True)
    else:
        st.info("Histórico Fear & Greed disponível após execuções.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Agente de IA
# ══════════════════════════════════════════════════════════════════════════════
with tab5:

    agent: agent_module.CryptoAgent = st.session_state.crypto_agent

    # Modelo ativo — info rápida
    current_model = st.session_state.crypto_agent.model if "crypto_agent" in st.session_state else config.AI_DEFAULT_MODEL
    st.markdown(f'''
    <div style="background:#0d1526;border:1px solid #1a2744;border-radius:10px;
        padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;gap:10px">
      <div style="font-size:20px">🤖</div>
      <div>
        <div style="font-size:10px;color:#4a6080;letter-spacing:1px;text-transform:uppercase">Modelo ativo</div>
        <div style="font-family:Space Mono,monospace;font-size:13px;color:#60a5fa;font-weight:700">{current_model}</div>
        <div style="font-size:11px;color:#4a6080;margin-top:2px">Troque o modelo na sidebar ←</div>
      </div>
    </div>''', unsafe_allow_html=True)

    st.divider()

    results  = st.session_state.analysis_results
    has_data = bool(results)
    key_st   = agent_module.get_key_status()
    has_key  = any(key_st.values())

    if not has_data:
        st.markdown("""
        <div style="text-align:center;padding:40px 20px;color:#4a6080">
          <div style="font-size:40px;margin-bottom:12px">🤖</div>
          <div style="font-size:16px;color:#7a92b8;margin-bottom:6px">Agente aguardando dados</div>
          <div style="font-size:13px">Execute a análise técnica primeiro (sidebar → ▶ RODAR ANÁLISE COMPLETA)</div>
        </div>
        """, unsafe_allow_html=True)

    elif not has_key:
        st.warning("⚠️ Nenhuma API Key encontrada. Adicione suas keys no arquivo `.env` e reinicie o app.")

    else:
        # Garante que o contexto está carregado mesmo que o usuário não tenha
        # rodado a análise nesta sessão (dados já existiam)
        if not agent.market_context and results:
            agent.update_context(
                top_results   = results[:10],
                fear_greed    = st.session_state.fear_greed,
                global_market = st.session_state.global_market,
            )

        # ── Relatório automático ─────────────────────────────────────────────
        st.markdown('<div class="section-header">📋 Relatório do Agente — Top 10 do Dia</div>', unsafe_allow_html=True)

        col_rep1, col_rep2 = st.columns([5, 1])
        with col_rep2:
            gen_report = st.button("🔄 Gerar / Atualizar", key="gen_report", use_container_width=True)

        if gen_report or (not st.session_state.agent_report and has_data and has_key):
            with st.spinner("🤖 Analisando mercado e elaborando relatório..."):
                st.session_state.agent_report = agent.generate_report()

        if st.session_state.agent_report:
            st.markdown(f"""
            <div style="background:#0d1526;border:1px solid #1a2744;border-radius:12px;
                padding:24px 28px;line-height:1.75;font-size:14px;color:#c9d4e8;
                white-space:pre-wrap">
{st.session_state.agent_report}
            </div>
            """, unsafe_allow_html=True)

        st.divider()

        # ── Chat com o agente ────────────────────────────────────────────────
        st.markdown('<div class="section-header">💬 Chat com o Agente</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:12px;color:#4a6080;margin-bottom:16px">
        Faça perguntas específicas sobre qualquer ativo, cenário ou estratégia.
        O agente tem acesso a todos os dados da análise atual.
        </div>
        """, unsafe_allow_html=True)

        # Sugestões de perguntas rápidas
        st.markdown("**💡 Perguntas rápidas:**")
        quick_cols = st.columns(4)
        quick_questions = [
            "Qual o melhor momento para entrar no top 1?",
            "Tem alguma coin com divergência bullish?",
            "Quais coins têm volume confirmando a alta?",
            "O que o funding rate indica sobre o mercado agora?",
        ]
        for i, (col, q) in enumerate(zip(quick_cols, quick_questions)):
            with col:
                if st.button(q, key=f"quick_{i}", use_container_width=True):
                    with st.spinner("🤖 Pensando..."):
                        resp = agent.chat(q)
                    st.session_state.agent_chat = agent.chat_history.copy()
                    st.rerun()

        st.markdown("")

        # Histórico do chat
        chat_history = agent.chat_history
        if chat_history:
            for msg in chat_history:
                role    = msg["role"]
                content = msg["content"]

                if role == "user":
                    st.markdown(f"""
                    <div style="display:flex;justify-content:flex-end;margin-bottom:10px">
                      <div style="background:#1e3a5f;border:1px solid #2a4070;border-radius:12px 12px 2px 12px;
                          padding:12px 16px;max-width:75%;font-size:13px;color:#e2e8f0">
                        {content}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="display:flex;justify-content:flex-start;margin-bottom:10px;gap:10px">
                      <div style="font-size:20px;padding-top:4px">🤖</div>
                      <div style="background:#0d1526;border:1px solid #1a2744;border-radius:2px 12px 12px 12px;
                          padding:12px 16px;max-width:80%;font-size:13px;color:#c9d4e8;
                          line-height:1.65;white-space:pre-wrap">
{content}
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Input do usuário
        with st.form("chat_form", clear_on_submit=True):
            col_input, col_send = st.columns([5, 1])
            with col_input:
                user_input = st.text_input(
                    "Sua pergunta",
                    placeholder="Ex: Por que o SOL está com score alto? O que o ADX indica sobre o BTC?",
                    label_visibility="collapsed",
                )
            with col_send:
                send_btn = st.form_submit_button("Enviar ➤", use_container_width=True)

            if send_btn and user_input.strip():
                with st.spinner("🤖 Pensando..."):
                    agent.chat(user_input.strip())
                st.session_state.agent_chat = agent.chat_history.copy()
                st.rerun()

        # Botão limpar histórico
        if chat_history:
            if st.button("🗑️ Limpar conversa", key="clear_chat"):
                agent.clear_history()
                st.session_state.agent_chat = []
                st.rerun()
