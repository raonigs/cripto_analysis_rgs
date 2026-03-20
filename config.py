import os
# =============================================================================
# config.py — Configurações globais do sistema
# =============================================================================

# ---------------------------------------------------------------------------
# Watchlist padrão (pares USDT)
# ---------------------------------------------------------------------------
WATCHLIST = [
    # ── Large Cap — base sólida de mercado ──────────────────────────────────
    "BTC/USDT",   # Bitcoin — reserva de valor, líder absoluto
    "ETH/USDT",   # Ethereum — maior ecossistema DeFi/NFT
    "BNB/USDT",   # Binance Coin — token da maior exchange
    "SOL/USDT",   # Solana — L1 de alta performance
    "XRP/USDT",   # Ripple — pagamentos cross-border
    "ADA/USDT",   # Cardano — L1 acadêmico/peer-reviewed
    "AVAX/USDT",  # Avalanche — L1 modular com subnets
    "DOT/USDT",   # Polkadot — interoperabilidade cross-chain
    "LTC/USDT",   # Litecoin — pagamentos rápidos, OG
    "BCH/USDT",   # Bitcoin Cash — fork Bitcoin, pagamentos

    # ── Layer 2 & Scaling ────────────────────────────────────────────────────
    "MATIC/USDT", # Polygon — L2 Ethereum mais adotado
    "OP/USDT",    # Optimism — L2 Ethereum Optimistic Rollup
    "ARB/USDT",   # Arbitrum — L2 maior TVL em rollups
    "IMX/USDT",   # Immutable X — L2 focado em gaming/NFT
    "STRK/USDT",  # Starknet — L2 ZK Rollup Ethereum
    "MANTA/USDT", # Manta Network — L2 ZK com privacidade

    # ── DeFi Blue Chips ─────────────────────────────────────────────────────
    "LINK/USDT",  # Chainlink — oráculos, infraestrutura DeFi
    "UNI/USDT",   # Uniswap — maior DEX por volume
    "AAVE/USDT",  # Aave — líder em lending/borrowing
    "MKR/USDT",   # MakerDAO — protocolo DAI, DeFi OG
    "CRV/USDT",   # Curve Finance — DEX para stablecoins
    "LDO/USDT",   # Lido DAO — maior liquid staking ETH
    "PENDLE/USDT",# Pendle — yield tokenization, crescimento forte
    "EIGEN/USDT", # EigenLayer — restaking, narrativa 2024/25

    # ── Smart Contract Platforms / L1 alternativos ───────────────────────────
    "NEAR/USDT",  # NEAR Protocol — L1 sharding, UX amigável
    "APT/USDT",   # Aptos — L1 Move, ex-equipe Diem/Meta
    "SUI/USDT",   # Sui — L1 Move, alto throughput
    "SEI/USDT",   # Sei — L1 otimizado para trading
    "INJ/USDT",   # Injective — L1 DeFi/derivativos
    "TIA/USDT",   # Celestia — modular blockchain, DA layer
    "ATOM/USDT",  # Cosmos — hub interoperabilidade IBC
    "FTM/USDT",   # Fantom — L1 DAG rápido (Sonic upgrade)
    "ALGO/USDT",  # Algorand — L1 Pure PoS, foco em TradFi
    "TON/USDT",   # Toncoin — blockchain integrado Telegram

    # ── AI & Data ────────────────────────────────────────────────────────────
    "FET/USDT",   # Fetch.ai (ASI Alliance) — AI agents
    "RENDER/USDT",# Render Network — GPU rendering descentralizado
    "WLD/USDT",   # Worldcoin — identidade digital / Sam Altman
    "TAO/USDT",   # Bittensor — rede descentralizada de ML
    "AGIX/USDT",  # SingularityNET — marketplace de IA
    "GRT/USDT",   # The Graph — indexação de dados blockchain

    # ── Gaming & Metaverse ───────────────────────────────────────────────────
    "AXS/USDT",   # Axie Infinity — play-to-earn pioneiro
    "SAND/USDT",  # The Sandbox — metaverso com parceiros AAA
    "MANA/USDT",  # Decentraland — metaverso 3D
    "GALA/USDT",  # Gala Games — plataforma gaming Web3
    "BEAM/USDT",  # Beam — gaming chain (ex-Merit Circle)

    # ── RWA & Infraestrutura ─────────────────────────────────────────────────
    "OM/USDT",    # MANTRA — RWA tokenization, narrativa forte 2025
    "ONDO/USDT",  # Ondo Finance — tokenização de T-bills/RWA
    "CFG/USDT",   # Centrifuge — DeFi para ativos reais
    "SNX/USDT",   # Synthetix — derivativos sintéticos on-chain

    # ── Meme Coins de alta liquidez ──────────────────────────────────────────
    "DOGE/USDT",  # Dogecoin — maior meme coin, altíssima liquidez
    "SHIB/USDT",  # Shiba Inu — ecossistema crescente
    "PEPE/USDT",  # Pepe — meme coin top 3 por market cap
    "WIF/USDT",   # Dogwifhat — meme Solana líder
    "BONK/USDT",  # Bonk — meme original ecossistema Solana
    "FLOKI/USDT", # Floki — meme com utilidade real

    # ── Infraestrutura Web3 & Privacidade ────────────────────────────────────
    "JUP/USDT",   # Jupiter — maior DEX aggregator Solana
    "PYTH/USDT",  # Pyth Network — oráculos alta frequência
    "W/USDT",     # Wormhole — ponte cross-chain líder
    "ZRO/USDT",   # LayerZero — protocolo de mensagens cross-chain
    "HFT/USDT",   # Hashflow — DEX institucional cross-chain

    # ── Exchange Tokens ──────────────────────────────────────────────────────
    "OKB/USDT",   # OKX token — segunda maior exchange
    "CRO/USDT",   # Crypto.com — token com grande base de usuários
    "KCS/USDT",   # KuCoin Shares — exchange token relevante

    # ── DePIN (Decentralized Physical Infrastructure) ────────────────────────
    "HNT/USDT",   # Helium — rede wireless descentralizada
    "IOTX/USDT",  # IoTeX — IoT + blockchain
    "AIOZ/USDT",  # AIOZ Network — CDN e streaming descentralizado

    # ── Outros com alto volume e relevância ──────────────────────────────────
    "ICP/USDT",   # Internet Computer — computação on-chain
    "VET/USDT",   # VeChain — supply chain / enterprise
    "QNT/USDT",   # Quant — interoperabilidade enterprise
    "ENA/USDT",   # Ethena — protocolo de yield em stablecoin sintética
]

# ---------------------------------------------------------------------------
# Timeframes
# ---------------------------------------------------------------------------
TIMEFRAMES = {
    "1h":  "1h",
    "4h":  "4h",
    "1d":  "1d",
}
PRIMARY_TF   = "4h"   # Timeframe principal de análise
CANDLES_LIMIT = 200   # Candles buscados por requisição

# ---------------------------------------------------------------------------
# Indicadores — parâmetros
# ---------------------------------------------------------------------------
RSI_LENGTH       = 14
MACD_FAST        = 12
MACD_SLOW        = 26
MACD_SIGNAL      = 9
EMA_PERIODS      = [9, 21, 50, 200]
BB_LENGTH        = 20
BB_STD           = 2.0
STOCHRSI_LENGTH  = 14
ADX_LENGTH       = 14
ATR_LENGTH       = 14
VOLUME_SMA_LEN   = 20
OBV_EMA_LEN      = 21   # EMA da OBV para detectar tendência

# ---------------------------------------------------------------------------
# OCO — multiplicadores de ATR
# ---------------------------------------------------------------------------
ATR_TP_MULT_CONSERVADOR  = 1.8   # Take profit conservador
ATR_TP_MULT_MODERADO     = 2.5   # Take profit moderado (default)
ATR_TP_MULT_AGRESSIVO    = 3.5   # Take profit agressivo
ATR_SL_MULT              = 1.5   # Stop loss
STOP_LIMIT_OFFSET        = 0.003 # 0.3% abaixo do stop para o stop-limit

# ---------------------------------------------------------------------------
# Pesos do scoring — somam 100
# ---------------------------------------------------------------------------
WEIGHTS = {
    "rsi":          12,   # Sobrevendido/sobrecomprado
    "macd":         12,   # Momentum direcional
    "ema_trend":    10,   # Alinhamento das EMAs
    "bb_position":   8,   # Posição nas Bandas de Bollinger
    "stoch_rsi":     8,   # Stochastic RSI
    "adx":           8,   # Força da tendência
    "volume":        8,   # Volume relativo
    "obv_trend":     7,   # Tendência do OBV (confirmação de volume)
    "multi_tf":     12,   # Alinhamento multi-timeframe
    "fear_greed":    8,   # Índice Fear & Greed (sentimento macro)
    "funding_rate":  7,   # Funding rate (sentimento de alavancagem)
}
# Verificação: sum(WEIGHTS.values()) deve ser 100
assert sum(WEIGHTS.values()) == 100, "Pesos devem somar 100"

# ---------------------------------------------------------------------------
# Classificações de score
# ---------------------------------------------------------------------------
SCORE_LABELS = {
    (0,  40):  ("🔴 Fraco",      "red"),
    (40, 55):  ("🟡 Neutro",     "orange"),
    (55, 70):  ("🟢 Bom",        "green"),
    (70, 85):  ("💚 Forte",      "limegreen"),
    (85, 101): ("🚀 Excelente",  "cyan"),
}

# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------
DB_PATH = "crypto_analysis.db"

# ---------------------------------------------------------------------------
# APIs externas
# ---------------------------------------------------------------------------
FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1&format=json"
COINGECKO_GLOBAL_URL = "https://api.coingecko.com/api/v3/global"

# ---------------------------------------------------------------------------
# Streamlit — UI
# ---------------------------------------------------------------------------
PAGE_TITLE     = "Crypto Intelligence Dashboard"
PAGE_ICON      = "⚡"
AUTO_REFRESH_S = 300  # segundos entre auto-refreshes (0 = desligado)

# ---------------------------------------------------------------------------
# Agente de IA — API Keys carregadas do .env
# ---------------------------------------------------------------------------
# Crie um arquivo .env na raiz do projeto com suas keys:
#
#   GROQ_API_KEY=gsk_...
#   ANTHROPIC_API_KEY=sk-ant-...
#   OPENROUTER_API_KEY=sk-or-...
#   OPENAI_API_KEY=sk-...
#   HUGGINGFACE_API_KEY=hf_...
#   TOGETHER_API_KEY=...
#   MISTRAL_API_KEY=...
#
# O modelo é escolhido pelo usuário dentro do app (sidebar).
# Não é necessário editar este arquivo para trocar de modelo.

from dotenv import load_dotenv
load_dotenv()

# Keys lidas do .env — não edite aqui, edite o .env
AI_KEYS = {
    "groq":        os.getenv("GROQ_API_KEY", ""),
    "anthropic":   os.getenv("ANTHROPIC_API_KEY", ""),
    "openrouter":  os.getenv("OPENROUTER_API_KEY", ""),
    "openai":      os.getenv("OPENAI_API_KEY", ""),
    "huggingface": os.getenv("HUGGINGFACE_API_KEY", ""),
    "together":    os.getenv("TOGETHER_API_KEY", ""),
    "mistral":     os.getenv("MISTRAL_API_KEY", ""),
}

# Modelo padrão ao abrir o app (pode trocar na sidebar)
AI_DEFAULT_PROVIDER = "groq"
AI_DEFAULT_MODEL    = "groq/llama-3.3-70b-versatile"

AI_MAX_TOKENS   = 2000
AI_TEMPERATURE  = 0.7
AI_CHAT_HISTORY = 10

# ---------------------------------------------------------------------------
# Catálogo de modelos disponíveis por provedor
# ---------------------------------------------------------------------------
AI_MODELS_CATALOG = {
    "🟣  Groq  (gratuito)": {
        "provider": "groq",
        "env_key":  "groq",
        "models": {
            "Llama 3.3 70B  ⚡ recomendado":     "groq/llama-3.3-70b-versatile",
            "Llama 3.1 8B   ⚡ ultra rápido":     "groq/llama-3.1-8b-instant",
            "DeepSeek R1 70B  🧠 raciocínio":     "groq/deepseek-r1-distill-llama-70b",
            "Mixtral 8x7B   📚 contexto longo":   "groq/mixtral-8x7b-32768",
            "Gemma 2 9B":                          "groq/gemma2-9b-it",
        }
    },
    "🔵  Anthropic Claude  (pago)": {
        "provider": "anthropic",
        "env_key":  "anthropic",
        "models": {
            "Claude 3.5 Haiku  ⚡ rápido/barato": "claude-4-5-haiku-20251001",
            "Claude 3.5 Sonnet  🧠 melhor":       "claude-4-6-sonnet",
            "Claude 3 Opus  🏆 máxima qualidade": "claude-4-6-opus",
        }
    },
    "🟢  OpenRouter  (200+ modelos)": {
        "provider": "openrouter",
        "env_key":  "openrouter",
        "models": {
            "Gemini Flash 1.5  ⚡ rápido/grátis": "openrouter/google/gemini-flash-1.5",
            "Gemini Pro 1.5":                      "openrouter/google/gemini-pro-1.5",
            "Llama 3.3 70B  (grátis)":             "openrouter/meta-llama/llama-3.3-70b-instruct:free",
            "DeepSeek V3  (grátis)":               "openrouter/deepseek/deepseek-chat:free",
            "Mistral Large":                        "openrouter/mistralai/mistral-large",
            "Qwen 2.5 72B  (grátis)":              "openrouter/qwen/qwen-2.5-72b-instruct:free",
        }
    },
    "⚫  OpenAI  (pago)": {
        "provider": "openai",
        "env_key":  "openai",
        "models": {
            "GPT-4o Mini  ⚡ rápido/barato":       "gpt-4o-mini",
            "GPT-4o  🧠 melhor":                   "gpt-4o",
            "GPT-4 Turbo":                          "gpt-4-turbo",
            "o1 Mini  🧠 raciocínio":               "o1-mini",
        }
    },
    "🟡  Together AI  (pago)": {
        "provider": "together",
        "env_key":  "together",
        "models": {
            "Llama 3.3 70B":                        "together_ai/meta-llama/Llama-3.3-70B-Instruct-Turbo",
            "DeepSeek R1":                          "together_ai/deepseek-ai/DeepSeek-R1",
            "Mixtral 8x22B":                        "together_ai/mistralai/Mixtral-8x22B-Instruct-v0.1",
        }
    },
    "🟠  Mistral AI  (pago)": {
        "provider": "mistral",
        "env_key":  "mistral",
        "models": {
            "Mistral Large":                        "mistral/mistral-large-latest",
            "Mistral Small  ⚡ barato":             "mistral/mistral-small-latest",
            "Codestral":                            "mistral/codestral-latest",
        }
    },
    "🤗  HuggingFace  (grátis/pago)": {
        "provider": "huggingface",
        "env_key":  "huggingface",
        "models": {
            "Zephyr 7B Beta":                       "huggingface/HuggingFaceH4/zephyr-7b-beta",
            "Llama 3.1 8B":                         "huggingface/meta-llama/Meta-Llama-3.1-8B-Instruct",
        }
    },
}
