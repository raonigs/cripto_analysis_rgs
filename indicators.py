# =============================================================================
# indicators.py — Cálculo de todos os indicadores técnicos
# =============================================================================

import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Optional
import logging

from config import (
    RSI_LENGTH, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
    EMA_PERIODS, BB_LENGTH, BB_STD, STOCHRSI_LENGTH,
    ADX_LENGTH, ATR_LENGTH, VOLUME_SMA_LEN, OBV_EMA_LEN,
    ATR_TP_MULT_CONSERVADOR, ATR_TP_MULT_MODERADO,
    ATR_TP_MULT_AGRESSIVO, ATR_SL_MULT, STOP_LIMIT_OFFSET,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cálculo principal de indicadores (sobre DataFrame OHLCV)
# ---------------------------------------------------------------------------

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona todos os indicadores técnicos ao DataFrame OHLCV.
    O DataFrame deve ter colunas: open, high, low, close, volume
    """
    if df is None or len(df) < 50:
        return df

    df = df.copy()

    try:
        # ── RSI ────────────────────────────────────────────────────────────
        df["RSI"] = ta.rsi(df["close"], length=RSI_LENGTH)

        # ── MACD ───────────────────────────────────────────────────────────
        macd = ta.macd(df["close"], fast=MACD_FAST, slow=MACD_SLOW, signal=MACD_SIGNAL)
        if macd is not None and not macd.empty:
            df["MACD"]        = macd.iloc[:, 0]   # MACD line
            df["MACD_HIST"]   = macd.iloc[:, 1]   # Histogram
            df["MACD_SIGNAL"] = macd.iloc[:, 2]   # Signal line

        # ── EMAs ───────────────────────────────────────────────────────────
        for period in EMA_PERIODS:
            df[f"EMA{period}"] = ta.ema(df["close"], length=period)

        # ── Bandas de Bollinger ────────────────────────────────────────────
        bb = ta.bbands(df["close"], length=BB_LENGTH, std=BB_STD)
        if bb is not None and not bb.empty:
            df["BB_LOWER"]  = bb.iloc[:, 0]
            df["BB_MID"]    = bb.iloc[:, 1]
            df["BB_UPPER"]  = bb.iloc[:, 2]
            df["BB_WIDTH"]  = (df["BB_UPPER"] - df["BB_LOWER"]) / df["BB_MID"]
            df["BB_PCT"]    = (df["close"] - df["BB_LOWER"]) / (df["BB_UPPER"] - df["BB_LOWER"])
            # BB % position: 0 = at lower band, 1 = at upper band, 0.5 = at mid

        # ── Stochastic RSI ─────────────────────────────────────────────────
        stoch_rsi = ta.stochrsi(df["close"], length=STOCHRSI_LENGTH)
        if stoch_rsi is not None and not stoch_rsi.empty:
            df["STOCHRSI_K"] = stoch_rsi.iloc[:, 0]
            df["STOCHRSI_D"] = stoch_rsi.iloc[:, 1]

        # ── ADX + DI ───────────────────────────────────────────────────────
        adx = ta.adx(df["high"], df["low"], df["close"], length=ADX_LENGTH)
        if adx is not None and not adx.empty:
            df["ADX"]      = adx.iloc[:, 0]
            df["ADX_POS"]  = adx.iloc[:, 1]   # +DI (pressão compradora)
            df["ADX_NEG"]  = adx.iloc[:, 2]   # −DI (pressão vendedora)

        # ── ATR (volatilidade / cálculo OCO) ──────────────────────────────
        df["ATR"] = ta.atr(df["high"], df["low"], df["close"], length=ATR_LENGTH)

        # ── OBV + EMA da OBV ──────────────────────────────────────────────
        df["OBV"]     = ta.obv(df["close"], df["volume"])
        df["OBV_EMA"] = ta.ema(df["OBV"], length=OBV_EMA_LEN)

        # ── Volume SMA e Volume Ratio ──────────────────────────────────────
        df["VOL_SMA"]   = ta.sma(df["volume"], length=VOLUME_SMA_LEN)
        df["VOL_RATIO"] = df["volume"] / df["VOL_SMA"]

        # ── VWAP (Volume Weighted Average Price) ──────────────────────────
        # VWAP diário: requer reset por sessão; aqui calculamos VWAP rolling
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        df["VWAP"] = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()

        # ── Momentum (ROC) ─────────────────────────────────────────────────
        df["ROC_10"] = ta.roc(df["close"], length=10)

        # ── Williams %R ────────────────────────────────────────────────────
        df["WILLR"] = ta.willr(df["high"], df["low"], df["close"], length=14)

        # ── CCI (Commodity Channel Index) ─────────────────────────────────
        df["CCI"] = ta.cci(df["high"], df["low"], df["close"], length=20)

        # ── Candle direction e body size ───────────────────────────────────
        df["CANDLE_UP"]   = df["close"] > df["open"]
        df["CANDLE_BODY"] = abs(df["close"] - df["open"])
        df["CANDLE_RANGE"]= df["high"] - df["low"]

    except Exception as e:
        logger.error(f"Erro ao calcular indicadores: {e}")

    return df


# ---------------------------------------------------------------------------
# Leitura dos valores do último candle fechado
# ---------------------------------------------------------------------------

def get_last_values(df: pd.DataFrame) -> dict:
    """
    Extrai os valores mais recentes de todos os indicadores.
    Retorna um dict com os valores do último candle.
    """
    if df is None or df.empty:
        return {}

    row = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else row

    vals = {}
    for col in df.columns:
        val = row.get(col, None)
        vals[col] = float(val) if pd.notna(val) else None

    # Flags derivadas úteis para o scoring
    # MACD crossover: último MACD > Signal E antes MACD < Signal
    if all(c in df.columns for c in ["MACD", "MACD_SIGNAL"]):
        vals["MACD_CROSSOVER_UP"] = (
            row["MACD"] > row["MACD_SIGNAL"] and
            prev["MACD"] <= prev["MACD_SIGNAL"]
        )
        vals["MACD_CROSSOVER_DOWN"] = (
            row["MACD"] < row["MACD_SIGNAL"] and
            prev["MACD"] >= prev["MACD_SIGNAL"]
        )

    # StochRSI bullish crossover (K cruza acima de D na zona sobrevendida)
    if all(c in df.columns for c in ["STOCHRSI_K", "STOCHRSI_D"]):
        vals["STOCHRSI_BULL_CROSS"] = (
            row["STOCHRSI_K"] > row["STOCHRSI_D"] and
            prev["STOCHRSI_K"] <= prev["STOCHRSI_D"] and
            row["STOCHRSI_K"] < 30
        )

    # OBV tendência: OBV acima da EMA = bullish
    if all(c in df.columns for c in ["OBV", "OBV_EMA"]):
        vals["OBV_BULLISH"] = (row["OBV"] > row["OBV_EMA"]) if pd.notna(row.get("OBV_EMA")) else None

    # Preço acima do VWAP
    if "VWAP" in df.columns:
        vals["ABOVE_VWAP"] = row["close"] > row["VWAP"] if pd.notna(row.get("VWAP")) else None

    # EMA alignment score: conta quantas EMAs estão abaixo do preço
    ema_cols = [f"EMA{p}" for p in EMA_PERIODS if f"EMA{p}" in df.columns]
    emas_below = sum(1 for col in ema_cols if pd.notna(row.get(col)) and row["close"] > row[col])
    vals["EMA_ALIGNMENT_COUNT"] = emas_below   # 0-4
    vals["EMA_PERFECT_BULL"]    = emas_below == len(EMA_PERIODS)

    # DI trend: +DI > -DI = pressão compradora dominante
    if all(c in df.columns for c in ["ADX_POS", "ADX_NEG"]):
        vals["DI_BULLISH"] = (row["ADX_POS"] > row["ADX_NEG"]) if pd.notna(row.get("ADX_POS")) else None

    return vals


# ---------------------------------------------------------------------------
# Cálculo de parâmetros OCO
# ---------------------------------------------------------------------------

def calc_oco_params(df: pd.DataFrame, price: float) -> dict:
    """
    Calcula parâmetros OCO (entry, take profit, stop loss) baseados no ATR.
    Retorna dict com três cenários: conservador, moderado, agressivo.
    """
    if df is None or df.empty or "ATR" not in df.columns:
        return {}

    atr = df["ATR"].iloc[-1]
    if pd.isna(atr) or atr == 0:
        return {}

    entry = price

    # Três cenários de take profit
    scenarios = {}
    for name, tp_mult in [
        ("conservador", ATR_TP_MULT_CONSERVADOR),
        ("moderado",    ATR_TP_MULT_MODERADO),
        ("agressivo",   ATR_TP_MULT_AGRESSIVO),
    ]:
        tp    = entry + (atr * tp_mult)
        sl    = entry - (atr * ATR_SL_MULT)
        sl_lmt= sl    * (1 - STOP_LIMIT_OFFSET)   # stop-limit ligeiramente abaixo
        rr    = (tp - entry) / (entry - sl)

        # Lucro e risco percentuais
        tp_pct = (tp - entry) / entry * 100
        sl_pct = (entry - sl) / entry * 100

        scenarios[name] = {
            "entry":       round(entry, 6),
            "take_profit": round(tp, 6),
            "stop_loss":   round(sl, 6),
            "stop_limit":  round(sl_lmt, 6),
            "rr_ratio":    round(rr, 2),
            "tp_pct":      round(tp_pct, 2),
            "sl_pct":      round(sl_pct, 2),
            "atr":         round(atr, 6),
        }

    return scenarios


# ---------------------------------------------------------------------------
# Análise de suporte e resistência (pivot points simples)
# ---------------------------------------------------------------------------

def calc_support_resistance(df: pd.DataFrame, lookback: int = 20) -> dict:
    """
    Identifica níveis de suporte e resistência recentes usando pivot points.
    """
    if df is None or len(df) < lookback:
        return {}

    recent = df.tail(lookback)
    pivot  = (recent["high"].iloc[-1] + recent["low"].iloc[-1] + recent["close"].iloc[-1]) / 3

    r1 = 2 * pivot - recent["low"].iloc[-1]
    r2 = pivot + (recent["high"].iloc[-1] - recent["low"].iloc[-1])
    s1 = 2 * pivot - recent["high"].iloc[-1]
    s2 = pivot - (recent["high"].iloc[-1] - recent["low"].iloc[-1])

    # Máximos e mínimos recentes como zonas de S/R
    recent_high = recent["high"].max()
    recent_low  = recent["low"].min()

    return {
        "pivot":        round(pivot, 6),
        "resistance_1": round(r1, 6),
        "resistance_2": round(r2, 6),
        "support_1":    round(s1, 6),
        "support_2":    round(s2, 6),
        "period_high":  round(recent_high, 6),
        "period_low":   round(recent_low, 6),
    }


# ---------------------------------------------------------------------------
# Detecção de divergência RSI (bullish)
# ---------------------------------------------------------------------------

def detect_rsi_divergence(df: pd.DataFrame, lookback: int = 30) -> Optional[str]:
    """
    Detecta divergência bullish: preço faz mínimo mais baixo,
    mas RSI faz mínimo mais alto (sinal de reversão potencial).
    Retorna: 'bullish', 'bearish', ou None.
    """
    if df is None or len(df) < lookback or "RSI" not in df.columns:
        return None

    recent = df.tail(lookback).dropna(subset=["RSI"])
    if len(recent) < 5:
        return None

    # Últimos dois toques abaixo de 40
    lows_rsi = recent[recent["RSI"] < 45].copy()
    if len(lows_rsi) < 2:
        return None

    last   = lows_rsi.iloc[-1]
    second = lows_rsi.iloc[-2]

    # Bullish divergence: preço baixou mas RSI subiu
    if last["close"] < second["close"] and last["RSI"] > second["RSI"]:
        return "bullish"

    # Bearish divergence: preço subiu mas RSI caiu
    highs_rsi = recent[recent["RSI"] > 55].copy()
    if len(highs_rsi) >= 2:
        last_h   = highs_rsi.iloc[-1]
        second_h = highs_rsi.iloc[-2]
        if last_h["close"] > second_h["close"] and last_h["RSI"] < second_h["RSI"]:
            return "bearish"

    return None
