# =============================================================================
# scoring.py — Motor de scoring / probabilidade de alta
# =============================================================================

import pandas as pd
import numpy as np
from typing import Optional
import logging

from config import WEIGHTS, SCORE_LABELS, EMA_PERIODS
from indicators import compute_indicators, get_last_values, detect_rsi_divergence

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Funções de pontuação individuais (retornam 0.0 a 1.0)
# ---------------------------------------------------------------------------

def _score_rsi(vals: dict) -> tuple[float, str]:
    """RSI: zona de recuperação de sobrevendido = melhor entrada."""
    rsi = vals.get("RSI")
    if rsi is None:
        return 0.5, "N/A"
    if rsi < 25:
        return 0.55, f"⚡ Extremamente sobrevendido ({rsi:.1f})"
    if rsi < 35:
        return 1.0,  f"✅ Sobrevendido ({rsi:.1f})"
    if rsi < 50:
        return 0.85, f"🟢 Zona de recuperação ({rsi:.1f})"
    if rsi < 58:
        return 0.70, f"🔵 Momentum neutro ({rsi:.1f})"
    if rsi < 65:
        return 0.50, f"🟡 Momentum alto ({rsi:.1f})"
    if rsi < 72:
        return 0.25, f"🟠 Sobrecomprado ({rsi:.1f})"
    return 0.05,     f"🔴 Extremamente sobrecomprado ({rsi:.1f})"


def _score_macd(vals: dict) -> tuple[float, str]:
    """MACD: crossover bullish = máxima pontuação."""
    macd    = vals.get("MACD")
    signal  = vals.get("MACD_SIGNAL")
    hist    = vals.get("MACD_HIST")
    cross_up   = vals.get("MACD_CROSSOVER_UP", False)
    cross_down = vals.get("MACD_CROSSOVER_DOWN", False)

    if any(v is None for v in [macd, signal, hist]):
        return 0.5, "N/A"

    if cross_up:
        return 1.0, "✅ Crossover bullish acabou de acontecer"
    if cross_down:
        return 0.05, "🔴 Crossover bearish acabou de acontecer"

    if macd > signal and hist > 0:
        # Histograma crescendo?
        return 0.80, f"🟢 MACD acima do sinal, positivo"
    if macd > signal and hist < 0:
        return 0.65, f"🔵 MACD acima do sinal, zona negativa (convergindo)"
    if macd < signal and hist < 0:
        hist_abs = abs(hist)
        # Histograma encolhendo = potencial reversão
        score = 0.30 if hist_abs > 0.001 else 0.45
        return score, f"🟠 MACD abaixo do sinal"
    return 0.20, "🔴 MACD bearish"


def _score_ema_trend(vals: dict) -> tuple[float, str]:
    """Alinhamento das EMAs: price > EMA9 > EMA21 > EMA50 > EMA200."""
    count = vals.get("EMA_ALIGNMENT_COUNT", 0)
    perfect = vals.get("EMA_PERFECT_BULL", False)

    if perfect:
        return 1.0, "✅ Alinhamento perfeito: preço > EMA9 > 21 > 50 > 200"
    mapping = {
        4: (1.00, "✅ Preço acima de todas as EMAs"),
        3: (0.80, "🟢 Preço acima de EMA9, 21 e 50"),
        2: (0.55, "🔵 Preço acima de EMA9 e 21"),
        1: (0.30, "🟠 Preço apenas acima da EMA9"),
        0: (0.05, "🔴 Preço abaixo de todas as EMAs"),
    }
    s, label = mapping.get(count, (0.3, "?"))
    return s, label


def _score_bb_position(vals: dict) -> tuple[float, str]:
    """Posição nas Bandas de Bollinger."""
    bb_pct   = vals.get("BB_PCT")
    bb_width = vals.get("BB_WIDTH")

    if bb_pct is None:
        return 0.5, "N/A"

    squeeze = bb_width is not None and bb_width < 0.05  # BB estreitas = potencial explosão

    if bb_pct <= 0.05:
        note = " + Squeeze!" if squeeze else ""
        return 1.0,  f"✅ Tocando banda inferior{note} ({bb_pct:.2f})"
    if bb_pct <= 0.25:
        return 0.85, f"🟢 Zona inferior das BBands ({bb_pct:.2f})"
    if bb_pct <= 0.45:
        return 0.65, f"🔵 Abaixo da média das BBands ({bb_pct:.2f})"
    if bb_pct <= 0.55:
        note = " (Squeeze!)" if squeeze else ""
        return 0.50, f"🔵 Na média das BBands{note} ({bb_pct:.2f})"
    if bb_pct <= 0.75:
        return 0.35, f"🟡 Zona superior das BBands ({bb_pct:.2f})"
    if bb_pct <= 0.95:
        return 0.15, f"🟠 Próximo à banda superior ({bb_pct:.2f})"
    return 0.05,     f"🔴 Acima da banda superior ({bb_pct:.2f})"


def _score_stoch_rsi(vals: dict) -> tuple[float, str]:
    """StochRSI: crossover bullish na zona sobrevendida = melhor."""
    k     = vals.get("STOCHRSI_K")
    d     = vals.get("STOCHRSI_D")
    cross = vals.get("STOCHRSI_BULL_CROSS", False)

    if k is None or d is None:
        return 0.5, "N/A"

    if cross:
        return 1.0, f"✅ Crossover bullish sobrevendido (K={k:.1f})"
    if k < 20 and k > d:
        return 0.90, f"🟢 Sobrevendido, K acima de D (K={k:.1f})"
    if k < 20:
        return 0.75, f"🟢 Sobrevendido (K={k:.1f})"
    if k < 40:
        return 0.55, f"🔵 Zona baixa (K={k:.1f})"
    if k < 60:
        return 0.40, f"🟡 Neutro (K={k:.1f})"
    if k < 80:
        return 0.20, f"🟠 Zona alta (K={k:.1f})"
    return 0.05,     f"🔴 Sobrecomprado (K={k:.1f})"


def _score_adx(vals: dict) -> tuple[float, str]:
    """ADX: força da tendência + direção pelo DI."""
    adx        = vals.get("ADX")
    di_bullish = vals.get("DI_BULLISH")

    if adx is None:
        return 0.5, "N/A"

    direction_bonus = 1.0 if di_bullish else 0.6  # bônus se +DI > -DI

    if adx >= 40:
        base = 0.95
        return min(1.0, base * direction_bonus), f"✅ Tendência muito forte (ADX={adx:.1f})"
    if adx >= 25:
        base = 0.75
        return base * direction_bonus, f"🟢 Tendência forte (ADX={adx:.1f})"
    if adx >= 18:
        return 0.50, f"🟡 Tendência moderada (ADX={adx:.1f})"
    return 0.20, f"🟠 Tendência fraca / ranging (ADX={adx:.1f})"


def _score_volume(vals: dict) -> tuple[float, str]:
    """Volume relativo: volume alto em candle de alta = confirmação."""
    vol_ratio  = vals.get("VOL_RATIO")
    candle_up  = vals.get("CANDLE_UP", True)

    if vol_ratio is None:
        return 0.5, "N/A"

    if vol_ratio >= 2.5 and candle_up:
        return 1.0,  f"✅ Volume muito alto em alta (×{vol_ratio:.1f})"
    if vol_ratio >= 1.5 and candle_up:
        return 0.80, f"🟢 Volume acima da média em alta (×{vol_ratio:.1f})"
    if vol_ratio >= 1.0:
        return 0.55, f"🔵 Volume na média (×{vol_ratio:.1f})"
    if vol_ratio >= 0.7:
        return 0.35, f"🟡 Volume abaixo da média (×{vol_ratio:.1f})"
    return 0.15,     f"🔴 Volume muito baixo (×{vol_ratio:.1f})"


def _score_obv(vals: dict) -> tuple[float, str]:
    """OBV vs EMA da OBV: confirma acumulação ou distribuição."""
    obv_bullish  = vals.get("OBV_BULLISH")
    above_vwap   = vals.get("ABOVE_VWAP")

    score = 0.5
    notes = []

    if obv_bullish is True:
        score += 0.35
        notes.append("OBV acima da EMA (acumulação)")
    elif obv_bullish is False:
        score -= 0.30
        notes.append("OBV abaixo da EMA (distribuição)")

    if above_vwap is True:
        score += 0.15
        notes.append("preço acima do VWAP")
    elif above_vwap is False:
        score -= 0.10
        notes.append("preço abaixo do VWAP")

    score = max(0.0, min(1.0, score))
    emoji = "✅" if score > 0.7 else "🟢" if score > 0.55 else "🟡" if score > 0.4 else "🔴"
    label = f"{emoji} " + (", ".join(notes) if notes else "N/A")
    return score, label


def _score_multi_tf(tf_signals: dict) -> tuple[float, str]:
    """
    Multi-timeframe: alinhamento de 1h + 4h + 1d.
    Cada TF é bullish se: EMA9 > EMA21, MACD > Signal, RSI > 45.
    """
    if not tf_signals:
        return 0.5, "N/A"

    bullish_count = sum(1 for v in tf_signals.values() if v)
    total = len(tf_signals)
    ratio = bullish_count / total if total > 0 else 0

    details = " | ".join([
        f"{tf}:{'🟢' if bull else '🔴'}"
        for tf, bull in tf_signals.items()
    ])

    if ratio == 1.0:
        return 1.0, f"✅ Todos os TFs bullish — {details}"
    if ratio >= 0.67:
        return 0.75, f"🟢 Maioria bullish — {details}"
    if ratio >= 0.34:
        return 0.45, f"🟡 Sinais mistos — {details}"
    return 0.15, f"🔴 Maioria bearish — {details}"


def _score_fear_greed(fg_value: int) -> tuple[float, str]:
    """Fear & Greed: sentimento contrário — medo extremo = oportunidade."""
    if fg_value <= 15:
        return 1.0,  f"✅ Medo extremo ({fg_value}) — melhor momento para comprar"
    if fg_value <= 30:
        return 0.85, f"🟢 Medo ({fg_value}) — oportunidade de entrada"
    if fg_value <= 45:
        return 0.65, f"🔵 Leve medo ({fg_value})"
    if fg_value <= 55:
        return 0.50, f"🟡 Neutro ({fg_value})"
    if fg_value <= 70:
        return 0.35, f"🟠 Ganância ({fg_value}) — cuidado"
    if fg_value <= 85:
        return 0.15, f"🔴 Ganância alta ({fg_value}) — alto risco"
    return 0.05,     f"🔴 Ganância extrema ({fg_value}) — evitar novas entradas"


def _score_funding_rate(funding: Optional[float]) -> tuple[float, str]:
    """
    Funding rate: negativo extremo (shorts pagando) = potencial short squeeze.
    Positivo extremo = mercado sobrelavancado em long = risco de liquidação.
    """
    if funding is None:
        return 0.50, "N/A (futuros indisponível)"

    pct = funding * 100  # converte para %

    if pct < -0.10:
        return 1.0,  f"✅ Funding muito negativo ({pct:.3f}%) — shorts sobrecarregados"
    if pct < -0.03:
        return 0.80, f"🟢 Funding negativo ({pct:.3f}%) — pressão shorts"
    if abs(pct) <= 0.03:
        return 0.55, f"🔵 Funding neutro ({pct:.3f}%)"
    if pct < 0.07:
        return 0.40, f"🟡 Funding positivo ({pct:.3f}%) — leve alavancagem long"
    if pct < 0.12:
        return 0.20, f"🟠 Funding alto ({pct:.3f}%) — longs alavancados"
    return 0.05,     f"🔴 Funding muito alto ({pct:.3f}%) — risco de liquidação longs"


# ---------------------------------------------------------------------------
# Função auxiliar: determina se um TF é bullish
# ---------------------------------------------------------------------------

def _is_tf_bullish(df: pd.DataFrame) -> bool:
    """Retorna True se o timeframe exibe sinais predominantemente bullish."""
    if df is None or len(df) < 30:
        return False
    try:
        df_ind = compute_indicators(df)
        vals   = get_last_values(df_ind)
        score  = 0
        if vals.get("RSI", 50) > 45:
            score += 1
        if vals.get("MACD") is not None and vals.get("MACD_SIGNAL") is not None:
            if vals["MACD"] > vals["MACD_SIGNAL"]:
                score += 1
        if (vals.get("EMA_ALIGNMENT_COUNT", 0) or 0) >= 2:
            score += 1
        return score >= 2
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Score composto
# ---------------------------------------------------------------------------

def compute_score(
    df_primary: pd.DataFrame,
    tf_ohlcv:   dict,
    fear_greed: int,
    funding_rate: Optional[float],
) -> dict:
    """
    Calcula o score composto (0-100) para um ativo.
    
    Parâmetros:
        df_primary   — DataFrame com indicadores calculados (timeframe primário)
        tf_ohlcv     — dict {'1h': df, '4h': df, '1d': df} candles brutos
        fear_greed   — valor Fear & Greed (0-100)
        funding_rate — taxa de funding atual
    
    Retorna dict com score total, sub-scores e justificativas.
    """
    if df_primary is None or df_primary.empty:
        return {"total": 0, "details": {}, "error": "Dados insuficientes"}

    vals = get_last_values(df_primary)

    # Multi-TF signals
    tf_signals = {
        tf: _is_tf_bullish(df)
        for tf, df in tf_ohlcv.items()
    }

    # Calcula cada componente
    sub_scores = {}
    details    = {}

    funcs = {
        "rsi":         lambda: _score_rsi(vals),
        "macd":        lambda: _score_macd(vals),
        "ema_trend":   lambda: _score_ema_trend(vals),
        "bb_position": lambda: _score_bb_position(vals),
        "stoch_rsi":   lambda: _score_stoch_rsi(vals),
        "adx":         lambda: _score_adx(vals),
        "volume":      lambda: _score_volume(vals),
        "obv_trend":   lambda: _score_obv(vals),
        "multi_tf":    lambda: _score_multi_tf(tf_signals),
        "fear_greed":  lambda: _score_fear_greed(fear_greed),
        "funding_rate":lambda: _score_funding_rate(funding_rate),
    }

    for key, func in funcs.items():
        try:
            norm_score, label = func()
            weighted = norm_score * WEIGHTS[key]
            sub_scores[key] = {
                "raw":        round(norm_score * 100, 1),
                "weighted":   round(weighted, 2),
                "max_weight": WEIGHTS[key],
                "label":      label,
            }
        except Exception as e:
            logger.warning(f"Erro no score de {key}: {e}")
            sub_scores[key] = {"raw": 50, "weighted": WEIGHTS[key] * 0.5, "label": "Erro"}

    total = sum(v["weighted"] for v in sub_scores.values())
    total = round(min(100, max(0, total)), 1)

    # Bônus por divergência RSI bullish
    divergence = detect_rsi_divergence(df_primary)
    div_bonus  = 3.0 if divergence == "bullish" else (-2.0 if divergence == "bearish" else 0)
    total      = round(min(100, max(0, total + div_bonus)), 1)

    # Label do score
    score_label, score_color = "Neutro", "gray"
    for (low, high), (label, color) in SCORE_LABELS.items():
        if low <= total < high:
            score_label, score_color = label, color
            break

    return {
        "total":       total,
        "label":       score_label,
        "color":       score_color,
        "sub_scores":  sub_scores,
        "divergence":  divergence,
        "div_bonus":   div_bonus,
        "tf_signals":  tf_signals,
        "last_vals":   vals,
    }
