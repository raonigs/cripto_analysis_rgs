# =============================================================================
# data_collector.py — Coleta de dados: Binance (ccxt) + APIs externas
# =============================================================================

import ccxt
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Optional
import time
import logging

from config import (
    CANDLES_LIMIT, TIMEFRAMES, PRIMARY_TF,
    FEAR_GREED_URL, COINGECKO_GLOBAL_URL
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exchange — instância global (sem autenticação para dados públicos)
# ---------------------------------------------------------------------------
_exchange: Optional[ccxt.binance] = None


def get_exchange() -> ccxt.binance:
    global _exchange
    if _exchange is None:
        _exchange = ccxt.binance({
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })
    return _exchange


def get_futures_exchange() -> ccxt.binance:
    """Instância separada para dados de futuros (funding rate, OI)."""
    return ccxt.binance({
        "enableRateLimit": True,
        "options": {"defaultType": "future"},
    })


# ---------------------------------------------------------------------------
# OHLCV
# ---------------------------------------------------------------------------

def fetch_ohlcv(symbol: str, timeframe: str = PRIMARY_TF,
                limit: int = CANDLES_LIMIT) -> pd.DataFrame:
    """
    Busca candles OHLCV da Binance.
    Retorna DataFrame com colunas: timestamp, open, high, low, close, volume
    """
    try:
        exchange = get_exchange()
        raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df = df.set_index("timestamp").astype(float)
        return df
    except ccxt.BadSymbol:
        logger.warning(f"Símbolo não encontrado: {symbol}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Erro ao buscar OHLCV {symbol}/{timeframe}: {e}")
        return pd.DataFrame()


def fetch_multi_timeframe(symbol: str) -> dict[str, pd.DataFrame]:
    """
    Busca OHLCV nos três timeframes (1h, 4h, 1d).
    Retorna dict {'1h': df, '4h': df, '1d': df}
    """
    result = {}
    for tf_key, tf_val in TIMEFRAMES.items():
        df = fetch_ohlcv(symbol, timeframe=tf_val)
        if not df.empty:
            result[tf_key] = df
        time.sleep(0.1)  # rate limit gentil
    return result


# ---------------------------------------------------------------------------
# Ticker (preço atual + variação 24h)
# ---------------------------------------------------------------------------

def fetch_ticker(symbol: str) -> dict:
    """Retorna preço atual, variação 24h, volume 24h."""
    try:
        exchange = get_exchange()
        t = exchange.fetch_ticker(symbol)
        return {
            "price":        t.get("last", 0),
            "change_24h":   t.get("percentage", 0),
            "volume_24h":   t.get("quoteVolume", 0),
            "high_24h":     t.get("high", 0),
            "low_24h":      t.get("low", 0),
            "bid":          t.get("bid", 0),
            "ask":          t.get("ask", 0),
        }
    except Exception as e:
        logger.error(f"Erro ticker {symbol}: {e}")
        return {}


# ---------------------------------------------------------------------------
# Funding Rate (Futuros Perpétuos)
# ---------------------------------------------------------------------------

def fetch_funding_rate(symbol: str) -> Optional[float]:
    """
    Retorna o funding rate atual do contrato perpétuo.
    Positivo = longs pagam shorts (mercado bullish/alavancado em long)
    Negativo = shorts pagam longs (mercado bearish/alavancado em short)
    """
    try:
        futures = get_futures_exchange()
        # Converte símbolo spot para futuros: "BTC/USDT" -> "BTC/USDT:USDT"
        futures_symbol = symbol.replace("/USDT", "/USDT:USDT")
        data = futures.fetch_funding_rate(futures_symbol)
        rate = data.get("fundingRate", None)
        return float(rate) if rate is not None else None
    except Exception as e:
        logger.debug(f"Funding rate indisponível para {symbol}: {e}")
        return None


def fetch_open_interest(symbol: str) -> Optional[float]:
    """Retorna o Open Interest atual em USD."""
    try:
        futures = get_futures_exchange()
        futures_symbol = symbol.replace("/USDT", "/USDT:USDT")
        data = futures.fetch_open_interest(futures_symbol)
        return float(data.get("openInterestValue", 0))
    except Exception as e:
        logger.debug(f"Open Interest indisponível para {symbol}: {e}")
        return None


# ---------------------------------------------------------------------------
# Fear & Greed Index
# ---------------------------------------------------------------------------

def fetch_fear_greed() -> dict:
    """
    Retorna o Índice de Fear & Greed atual da alternative.me.
    Ex: {'value': 72, 'label': 'Greed', 'timestamp': '...'}
    """
    try:
        resp = requests.get(FEAR_GREED_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()["data"][0]
        return {
            "value":     int(data["value"]),
            "label":     data["value_classification"],
            "timestamp": data["timestamp"],
        }
    except Exception as e:
        logger.error(f"Erro Fear & Greed: {e}")
        return {"value": 50, "label": "Neutral", "timestamp": ""}


# ---------------------------------------------------------------------------
# Dominância do BTC + dados globais de mercado
# ---------------------------------------------------------------------------

def fetch_global_market() -> dict:
    """
    Retorna dados globais: dominância BTC/ETH, market cap total, volume 24h.
    Usa CoinGecko API (sem chave, pode ter rate limit leve).
    """
    try:
        resp = requests.get(COINGECKO_GLOBAL_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()["data"]
        return {
            "btc_dominance":       round(data["market_cap_percentage"].get("btc", 0), 2),
            "eth_dominance":       round(data["market_cap_percentage"].get("eth", 0), 2),
            "total_market_cap":    data["total_market_cap"].get("usd", 0),
            "total_volume_24h":    data["total_volume"].get("usd", 0),
            "market_cap_change":   round(data.get("market_cap_change_percentage_24h_usd", 0), 2),
            "active_coins":        data.get("active_cryptocurrencies", 0),
        }
    except Exception as e:
        logger.error(f"Erro dados globais CoinGecko: {e}")
        return {}


# ---------------------------------------------------------------------------
# Variações de preço multi-período (calculadas a partir dos candles)
# ---------------------------------------------------------------------------

def calc_price_changes(df_1h: pd.DataFrame, df_4h: pd.DataFrame,
                       df_1d: pd.DataFrame) -> dict:
    """
    Calcula variação percentual de preço em múltiplos períodos.
    """
    def pct_change_n(df: pd.DataFrame, n: int) -> float:
        if df is None or len(df) < n + 1:
            return 0.0
        current = df["close"].iloc[-1]
        past    = df["close"].iloc[-n - 1]
        return round((current - past) / past * 100, 2)

    return {
        "change_1h":  pct_change_n(df_1h, 1),
        "change_4h":  pct_change_n(df_4h, 1),
        "change_24h": pct_change_n(df_1d, 1),
        "change_7d":  pct_change_n(df_1d, 7),
        "change_30d": pct_change_n(df_1d, 30),
    }


# ---------------------------------------------------------------------------
# Coleta completa para um símbolo
# ---------------------------------------------------------------------------

def collect_all(symbol: str) -> dict:
    """
    Coleta todos os dados necessários para análise de um símbolo.
    Retorna dict com: ohlcv (dict de TFs), ticker, funding_rate, open_interest.
    """
    ohlcv    = fetch_multi_timeframe(symbol)
    ticker   = fetch_ticker(symbol)
    funding  = fetch_funding_rate(symbol)
    oi       = fetch_open_interest(symbol)

    price_changes = {}
    if all(tf in ohlcv for tf in ["1h", "4h", "1d"]):
        price_changes = calc_price_changes(
            ohlcv["1h"], ohlcv["4h"], ohlcv["1d"]
        )

    return {
        "symbol":        symbol,
        "ohlcv":         ohlcv,
        "ticker":        ticker,
        "funding_rate":  funding,
        "open_interest": oi,
        "price_changes": price_changes,
    }
