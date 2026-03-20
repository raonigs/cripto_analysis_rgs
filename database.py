# =============================================================================
# database.py — Persistência local com SQLite
# =============================================================================

import sqlite3
import json
import pandas as pd
from datetime import datetime
from config import DB_PATH


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Cria as tabelas se não existirem."""
    conn = _connect()
    cur = conn.cursor()

    # Tabela principal de análises
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol      TEXT    NOT NULL,
            timeframe   TEXT    NOT NULL,
            timestamp   TEXT    NOT NULL,
            score       REAL    NOT NULL,
            indicators  TEXT    NOT NULL,   -- JSON
            oco_params  TEXT    NOT NULL,   -- JSON
            price       REAL    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # Tabela de histórico do Fear & Greed
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fear_greed_history (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            value     INTEGER NOT NULL,
            label     TEXT    NOT NULL,
            timestamp TEXT    NOT NULL
        )
    """)

    # Tabela de resumos de execuções (snapshots do top-10)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT    DEFAULT (datetime('now')),
            top10_json TEXT    NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Analyses
# ---------------------------------------------------------------------------

def save_analysis(symbol: str, timeframe: str, score: float,
                  indicators: dict, oco_params: dict, price: float) -> None:
    conn = _connect()
    conn.execute("""
        INSERT INTO analyses (symbol, timeframe, timestamp, score, indicators, oco_params, price)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        symbol, timeframe,
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        round(score, 2),
        json.dumps(indicators),
        json.dumps(oco_params),
        round(price, 6),
    ))
    conn.commit()
    conn.close()


def get_history(symbol: str = None, limit: int = 100) -> pd.DataFrame:
    conn = _connect()
    if symbol:
        df = pd.read_sql_query(
            "SELECT * FROM analyses WHERE symbol=? ORDER BY id DESC LIMIT ?",
            conn, params=(symbol, limit)
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM analyses ORDER BY id DESC LIMIT ?",
            conn, params=(limit,)
        )
    conn.close()
    return df


def get_score_history(symbol: str, limit: int = 50) -> pd.DataFrame:
    """Retorna histórico de scores para um símbolo (para gráfico de evolução)."""
    conn = _connect()
    df = pd.read_sql_query(
        "SELECT timestamp, score, price FROM analyses WHERE symbol=? ORDER BY id DESC LIMIT ?",
        conn, params=(symbol, limit)
    )
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df.sort_values('timestamp')


# ---------------------------------------------------------------------------
# Snapshots (top-10 por execução)
# ---------------------------------------------------------------------------

def save_snapshot(top10: list) -> None:
    conn = _connect()
    conn.execute(
        "INSERT INTO snapshots (top10_json) VALUES (?)",
        (json.dumps(top10),)
    )
    conn.commit()
    conn.close()


def get_snapshots(limit: int = 20) -> list:
    conn = _connect()
    rows = conn.execute(
        "SELECT created_at, top10_json FROM snapshots ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [{"created_at": r["created_at"], "top10": json.loads(r["top10_json"])} for r in rows]


# ---------------------------------------------------------------------------
# Fear & Greed history
# ---------------------------------------------------------------------------

def save_fear_greed(value: int, label: str, timestamp: str) -> None:
    conn = _connect()
    conn.execute(
        "INSERT INTO fear_greed_history (value, label, timestamp) VALUES (?, ?, ?)",
        (value, label, timestamp)
    )
    conn.commit()
    conn.close()


def get_fear_greed_history(limit: int = 30) -> pd.DataFrame:
    conn = _connect()
    df = pd.read_sql_query(
        "SELECT timestamp, value, label FROM fear_greed_history ORDER BY id DESC LIMIT ?",
        conn, params=(limit,)
    )
    conn.close()

    # A API alternative.me retorna Unix epoch como string (ex: "1773792000")
    # Converte com segurança independente do formato salvo
    def _parse_ts(val):
        try:
            numeric = int(float(str(val)))
            if numeric > 1e12:
                return pd.to_datetime(numeric, unit='ms', utc=True)
            return pd.to_datetime(numeric, unit='s', utc=True)
        except (ValueError, TypeError, OSError):
            return pd.to_datetime(val, errors='coerce', utc=True)

    df['timestamp'] = df['timestamp'].apply(_parse_ts)
    return df.sort_values('timestamp')
