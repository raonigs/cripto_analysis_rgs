# ⚡ Crypto Intelligence Dashboard

Sistema de análise técnica multi-timeframe para criptomoedas, com scoring quantitativo e geração automática de parâmetros OCO para a Binance.

---

## 📦 Instalação

### 1. Criar ambiente virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

> ⚠️ Se tiver problemas com `pandas-ta`, tente:
> ```bash
> pip install pandas-ta --pre
> ```

### 3. Executar
```bash
streamlit run app.py
```

O navegador abre automaticamente em `http://localhost:8501`

---

## 🗂️ Estrutura do projeto

```
crypto_dashboard/
├── app.py              # Frontend Streamlit + lógica de UI
├── config.py           # Configurações, watchlist, pesos do scoring
├── data_collector.py   # Coleta de dados (Binance via ccxt, APIs externas)
├── indicators.py       # Cálculo de todos os indicadores técnicos
├── scoring.py          # Motor de scoring quantitativo (0-100)
├── database.py         # Persistência SQLite (histórico de análises)
├── requirements.txt
└── README.md
```

---

## 📊 Indicadores calculados

| Indicador | Descrição |
|-----------|-----------|
| **RSI (14)** | Índice de Força Relativa |
| **MACD (12/26/9)** | Moving Average Convergence Divergence |
| **EMA 9/21/50/200** | Médias Móveis Exponenciais |
| **Bollinger Bands (20, 2σ)** | Bandas de volatilidade |
| **Stochastic RSI (14)** | RSI estocástico (K e D) |
| **ADX + DI (14)** | Força e direção da tendência |
| **ATR (14)** | Average True Range (para cálculo OCO) |
| **OBV + EMA** | On-Balance Volume (confirmação de volume) |
| **VWAP** | Volume Weighted Average Price |
| **Volume Ratio** | Volume atual / SMA do volume |
| **ROC (10)** | Rate of Change (momentum) |
| **Williams %R (14)** | Índice Williams |
| **CCI (20)** | Commodity Channel Index |
| **Pivot Points** | Suporte e Resistência (S1, S2, R1, R2) |
| **Divergência RSI** | Detecção automática de divergência bullish/bearish |

---

## 🧠 Scoring (0-100)

O score composto é calculado por 11 componentes com pesos diferentes:

| Componente | Peso | O que avalia |
|------------|------|--------------|
| RSI | 12 | Zona de sobrevendido/sobrecomprado |
| MACD | 12 | Momentum direcional e crossovers |
| Alinhamento EMAs | 10 | Price > EMA9 > EMA21 > EMA50 > EMA200 |
| Bollinger Bands | 8 | Posição relativa nas bandas |
| Stochastic RSI | 8 | Crossover bullish na zona sobrevendida |
| ADX | 8 | Força da tendência + direção DI |
| Volume | 8 | Volume relativo em candle de alta |
| OBV / VWAP | 7 | Acumulação/distribuição + preço vs VWAP |
| Multi-Timeframe | 12 | Alinhamento 1h + 4h + 1d |
| Fear & Greed | 8 | Sentimento macro (contrário) |
| Funding Rate | 7 | Alavancagem do mercado de futuros |

**Bônus:** +3 pts por divergência bullish RSI, -2 pts por divergência bearish.

### Classificação do score:
- 🔴 **0–40**: Fraco — não operar
- 🟡 **40–55**: Neutro — aguardar
- 🟢 **55–70**: Bom — possível entrada
- 💚 **70–85**: Forte — setup interessante
- 🚀 **85–100**: Excelente — setup premium

---

## 📋 Parâmetros OCO

Três cenários baseados no ATR (Average True Range):

| Cenário | TP Mult | SL Mult | R:R aprox. |
|---------|---------|---------|-----------|
| 🛡️ Conservador | 1.8× ATR | 1.5× ATR | ~1.2 |
| ⚖️ Moderado | 2.5× ATR | 1.5× ATR | ~1.67 |
| 🚀 Agressivo | 3.5× ATR | 1.5× ATR | ~2.33 |

**Como usar no Binance Spot:**
1. Compre o ativo no preço de entrada
2. Vá em **Trade → Spot → OCO Order**
3. Preencha:
   - **Price**: Take Profit
   - **Stop**: Stop Loss  
   - **Limit**: Stop Limit (ligeiramente abaixo do stop)

---

## ⚙️ Personalização (config.py)

```python
# Adicionar/remover moedas da watchlist
WATCHLIST = ["BTC/USDT", "ETH/USDT", ...]

# Ajustar timeframe primário
PRIMARY_TF = "4h"   # opções: "1h", "4h", "1d"

# Ajustar multiplicadores OCO
ATR_TP_MULT_MODERADO = 2.5
ATR_SL_MULT          = 1.5

# Ajustar pesos do scoring (devem somar 100)
WEIGHTS = {
    "rsi": 12,
    "macd": 12,
    ...
}
```

---

## 🔄 Automação (opcional)

Para rodar a análise automaticamente em horários fixos, crie um arquivo `scheduler.py`:

```python
from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess

def run_analysis():
    # Lógica de análise sem UI (headless)
    from config import WATCHLIST, PRIMARY_TF
    import data_collector as dc
    import indicators as ind
    import scoring as sc
    import database as db
    # ... implementar conforme necessidade

scheduler = BlockingScheduler()
scheduler.add_job(run_analysis, 'cron', hour='9,13', minute='30')
scheduler.start()
```

Ou simplesmente deixe o dashboard aberto e clique em **▶ RODAR ANÁLISE COMPLETA** 
nos horários que preferir.

---

## 📡 Dados utilizados

| Fonte | Dado | Autenticação |
|-------|------|-------------|
| Binance (via ccxt) | OHLCV, ticker, funding rate | ❌ Não necessária |
| alternative.me | Fear & Greed Index | ❌ Não necessária |
| CoinGecko | Dominância BTC/ETH, market cap global | ❌ Não necessária |

> 💡 Todos os dados são públicos. Não é necessário criar conta ou obter API keys para usar o dashboard.

---

## 🐛 Troubleshooting

**Erro `ModuleNotFoundError: No module named 'pandas_ta'`:**
```bash
pip install pandas-ta --pre
```

**Erro de rate limit na Binance:**
O ccxt já gerencia os rate limits automaticamente. Se ocorrer, aguarde 1-2 minutos e tente novamente.

**Gráfico não aparece / dados vazios:**
Verifique sua conexão com a internet. Alguns indicadores precisam de mínimo 50 candles para calcular.
