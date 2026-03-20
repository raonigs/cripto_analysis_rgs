# =============================================================================
# ai_agent.py — Agente de IA para análise de mercado cripto
# Usa LiteLLM: suporta Anthropic, Groq, OpenRouter, OpenAI, HuggingFace, etc.
# =============================================================================

import os
import logging
from datetime import datetime

import litellm
from litellm import completion

from config import (
    AI_KEYS, AI_DEFAULT_MODEL, AI_MAX_TOKENS,
    AI_TEMPERATURE, AI_CHAT_HISTORY, AI_MODELS_CATALOG
)

logger = logging.getLogger(__name__)
litellm.suppress_debug_info = True


# ---------------------------------------------------------------------------
# Injeção de todas as keys disponíveis no ambiente
# ---------------------------------------------------------------------------

def load_all_keys() -> None:
    key_map = {
        "GROQ_API_KEY":        AI_KEYS.get("groq", ""),
        "ANTHROPIC_API_KEY":   AI_KEYS.get("anthropic", ""),
        "OPENROUTER_API_KEY":  AI_KEYS.get("openrouter", ""),
        "OPENAI_API_KEY":      AI_KEYS.get("openai", ""),
        "HUGGINGFACE_API_KEY": AI_KEYS.get("huggingface", ""),
        "TOGETHERAI_API_KEY":  AI_KEYS.get("together", ""),
        "MISTRAL_API_KEY":     AI_KEYS.get("mistral", ""),
    }
    for env_var, value in key_map.items():
        if value:
            os.environ[env_var] = value


def get_key_status() -> dict:
    """Retorna dict {display_name: bool} — True se tem key configurada."""
    status = {}
    for display_name, info in AI_MODELS_CATALOG.items():
        key = AI_KEYS.get(info["env_key"], "")
        status[display_name] = bool(key)
    return status


# ---------------------------------------------------------------------------
# Formatação do contexto de mercado
# ---------------------------------------------------------------------------

def _format_market_context(top_results, fear_greed, global_market) -> str:
    fg_val   = fear_greed.get("value", 50)
    fg_label = fear_greed.get("label", "Neutral")
    btc_dom  = global_market.get("btc_dominance", "N/A")
    mkt_chg  = global_market.get("market_cap_change", 0)

    lines = [
        "=== CONTEXTO DE MERCADO ===",
        f"Data/hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        f"Fear & Greed Index: {fg_val}/100 ({fg_label})",
        f"Dominância BTC: {btc_dom}%",
        f"Variação mercado 24h: {mkt_chg:+.2f}%",
        "",
        "=== TOP 10 ATIVOS — SCORES E INDICADORES ===",
    ]

    for i, r in enumerate(top_results[:10], 1):
        sym   = r["symbol"].replace("/USDT", "")
        score = r["score"]
        price = r["price"]
        pc    = r.get("price_changes", {})
        ind_v = r.get("indicators", {})
        sub   = r.get("sub_scores", {})
        fund  = r.get("funding_rate")
        div   = r.get("divergence")
        tf    = r.get("tf_signals", {})

        sub_txt = ", ".join([
            f"{k.upper()}={v['raw']:.0f}"
            for k, v in sub.items()
            if isinstance(v, dict) and "raw" in v
        ])
        tf_txt = " | ".join([
            f"{tf_k}:{'OK' if bull else 'X'}"
            for tf_k, bull in tf.items()
        ])

        lines += [
            f"\n{i}. {sym} — Score: {score:.1f}/100 | Preco: ${price:.4f}",
            f"   Variacoes: 1h={pc.get('change_1h',0):+.2f}% | 4h={pc.get('change_4h',0):+.2f}% | 24h={pc.get('change_24h',0):+.2f}% | 7d={pc.get('change_7d',0):+.2f}%",
            f"   RSI={ind_v.get('RSI',0):.1f} | ADX={ind_v.get('ADX',0):.1f} | BB%={ind_v.get('BB_PCT',0):.2f} | VolRatio={ind_v.get('VOL_RATIO',0):.2f}x",
            f"   Sub-scores: {sub_txt}",
            f"   Multi-TF: {tf_txt}",
            f"   Divergencia RSI: {div or 'nenhuma'} | Funding: {f'{fund*100:+.3f}%' if fund else 'N/A'}",
        ]

        oco = r.get("oco", {}).get("moderado", {})
        if oco:
            lines.append(
                f"   OCO moderado -> TP: ${oco.get('take_profit',0):.4f} (+{oco.get('tp_pct',0):.2f}%) | "
                f"SL: ${oco.get('stop_loss',0):.4f} (-{oco.get('sl_pct',0):.2f}%) | R:R={oco.get('rr_ratio',0):.2f}"
            )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Voce e um analista quantitativo especializado em mercado de criptomoedas, com profundo conhecimento em analise tecnica, gestao de risco e psicologia de mercado.

Seu papel e analisar os dados fornecidos e entregar insights praticos e honestos em portugues brasileiro.

PRINCIPIOS:
- Direto e objetivo, sem enrolacao
- Distingue claramente o que os dados mostram da sua interpretacao pessoal
- Sempre menciona RISCOS junto com oportunidades
- Nunca promete lucros — mercado cripto e imprevisivel
- Quando os dados sao fracos ou contraditorios, diz claramente "nao operaria agora"
- Linguagem acessivel sem perder precisao

ESTRUTURA DOS RELATORIOS:
1. Contexto macro (Fear & Greed, dominancia BTC, sentimento geral)
2. Top 3 picks do dia (analise especifica com numeros reais)
3. Alertas e riscos
4. O que voce faria: posicao pessoal clara e justificada
5. Outros destaques rapidos

QUANDO RESPONDER PERGUNTAS:
- Use os dados fornecidos para embasar as respostas
- Mantenha contexto do historico da conversa
"""


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class CryptoAgent:

    def __init__(self):
        self.chat_history:     list[dict] = []
        self.market_context:   str = ""
        self.model:            str = AI_DEFAULT_MODEL
        self._context_message: dict = {}
        self._context_ack:     dict = {}
        load_all_keys()

    def update_context(self, top_results, fear_greed, global_market) -> None:
        self.market_context = _format_market_context(top_results, fear_greed, global_market)
        self._context_message = {
            "role": "user",
            "content": f"[DADOS DA ANALISE]\n{self.market_context}\n\nUse estes dados como base."
        }
        self._context_ack = {
            "role": "assistant",
            "content": "Contexto recebido. Pronto para analisar."
        }

    def set_model(self, model_id: str) -> None:
        self.model = model_id
        load_all_keys()

    def generate_report(self) -> str:
        if not self.market_context:
            return "Nenhuma analise disponivel. Execute a analise tecnica primeiro."

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": self.market_context},
            {"role": "user",   "content": (
                "Com base nesses dados, gere o relatorio completo. "
                "Seja especifico, use os numeros reais. Ao final diga claramente em qual ativo "
                "voce apostaria agora (se apostaria), com qual cenario OCO e por que. "
                "Se nenhum te convencer, explique o que esperaria ver antes de entrar."
            )}
        ]

        try:
            resp = completion(
                model=self.model, messages=messages,
                max_tokens=AI_MAX_TOKENS, temperature=AI_TEMPERATURE,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error(f"Erro relatorio: {e}")
            return f"Erro ao comunicar com {self.model}:\n\n{e}\n\nVerifique se a API key esta no .env"

    def chat(self, user_message: str) -> str:
        if not user_message.strip():
            return ""

        self.chat_history.append({"role": "user", "content": user_message})
        history = self.chat_history[-(AI_CHAT_HISTORY * 2):]

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if self.market_context:
            messages += [self._context_message, self._context_ack]
        messages += history

        try:
            resp = completion(
                model=self.model, messages=messages,
                max_tokens=AI_MAX_TOKENS, temperature=AI_TEMPERATURE,
            )
            answer = resp.choices[0].message.content
        except Exception as e:
            logger.error(f"Erro chat: {e}")
            answer = f"Erro com {self.model}: {e}\n\nVerifique se a API key esta no .env"

        self.chat_history.append({"role": "assistant", "content": answer})
        return answer

    def clear_history(self) -> None:
        self.chat_history = []
