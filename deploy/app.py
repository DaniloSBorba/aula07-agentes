"""Gradio UI para Hugging Face Spaces.

Este é o entry point do Space. O arquivo é detectado automaticamente pelo HF
quando se chama `app.py` na raiz do Space.

Dois modos de execução expostos via abas:
  · Single ReAct  → rápido, trace visível
  · Multi LangGraph  → mais lento, mostra plan/context/draft/critique

A OPENAI_API_KEY vem como Secret do Space (NÃO commitar no código).
A variável PRODUCT vem como Variable do Space (educiacao ou designmind).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Resolver path para conseguir importar src/ no Space (cwd varia)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gradio as gr

from src.agents.multi_agent import run_multi_agent
from src.agents.single_agent import SingleAgent
from src.config import get_product_config

# Carrega config do produto ativo uma vez (espaço fica fixado em um produto)
_PRODUCT_CONFIG = get_product_config()
_PRODUCT_NAME = _PRODUCT_CONFIG["name"]
_EXAMPLE_PROMPTS = _PRODUCT_CONFIG["example_prompts"]


# =============================================================================
# Handlers
# =============================================================================
def handle_single(query: str) -> tuple[str, str]:
    """Roda agente single ReAct. Retorna (resposta_final, trace_markdown)."""
    if not query or len(query.strip()) < 3:
        return "Digite uma pergunta com pelo menos 3 caracteres.", ""

    agent = SingleAgent()
    result = agent.run(query, verbose=False)

    # Formata trace em markdown
    trace_lines = ["### Trace do agente\n"]
    for s in result.steps:
        if s.is_final:
            trace_lines.append(f"**Passo {s.step_number} · FINAL**")
            trace_lines.append(f"_resposta direta ao usuário (mostrada acima)_\n")
        else:
            args_str = json.dumps(s.tool_args or {}, ensure_ascii=False, indent=2)
            result_str = (s.tool_result or "")[:500]
            trace_lines.append(f"**Passo {s.step_number} · TOOL**")
            trace_lines.append(f"- ferramenta: `{s.tool_name}`")
            trace_lines.append(f"- argumentos: `{args_str}`")
            trace_lines.append(f"- resultado: {result_str}\n")

    return result.final_answer, "\n".join(trace_lines)


def handle_multi(query: str) -> tuple[str, str, str, str, str]:
    """Roda multi-agente. Retorna (final, plan, context, draft, critique)."""
    if not query or len(query.strip()) < 3:
        empty = "Digite uma pergunta com pelo menos 3 caracteres."
        return empty, "", "", "", ""

    state = run_multi_agent(query, max_iterations=2)
    return (
        state.get("final_answer", state.get("draft_answer", "")),
        state.get("plan", ""),
        state.get("context", "")[:2000],
        state.get("draft_answer", ""),
        state.get("critique", ""),
    )


# =============================================================================
# UI
# =============================================================================
INTRO = f"""
# {_PRODUCT_NAME}

Agente construído na Aula 07 do curso de Engenharia de IA.
Função calling nativa OpenAI + LangGraph + avaliação BFCL.

**Modelo**: {os.getenv("OPENAI_MODEL", "gpt-4.1-mini")} ·
**Produto ativo**: `{os.getenv("PRODUCT", "educiacao")}`

> Limitações deste Space gratuito: timeout de 30 segundos por requisição,
> sem persistência entre sessões, latência variável.
"""


with gr.Blocks(title=f"{_PRODUCT_NAME} · Agente") as demo:
    gr.Markdown(INTRO)

    with gr.Tabs():
        # ---------------------------------------------------------------------
        # Tab 1: Single ReAct
        # ---------------------------------------------------------------------
        with gr.Tab("Single ReAct · rápido"):
            gr.Markdown(
                "**Loop ReAct**: o LLM raciocina, chama tool, recebe resultado, "
                "itera até resposta final. Limite: 8 iterações."
            )
            with gr.Row():
                with gr.Column(scale=2):
                    s_input = gr.Textbox(
                        label="Sua pergunta",
                        placeholder=_EXAMPLE_PROMPTS[0],
                        lines=3,
                    )
                    gr.Examples(
                        examples=[[p] for p in _EXAMPLE_PROMPTS],
                        inputs=s_input,
                        label="Exemplos · clique para preencher",
                    )
                    s_button = gr.Button("Perguntar", variant="primary")
                with gr.Column(scale=3):
                    s_answer = gr.Textbox(
                        label="Resposta final",
                        lines=8,
                        interactive=False,
                    )
                    s_trace = gr.Markdown(label="Trace")

            s_button.click(
                fn=handle_single,
                inputs=s_input,
                outputs=[s_answer, s_trace],
            )

        # ---------------------------------------------------------------------
        # Tab 2: Multi LangGraph
        # ---------------------------------------------------------------------
        with gr.Tab("Multi LangGraph · estruturado"):
            gr.Markdown(
                "**Plan-and-execute com self-critique**: 4 nós sequenciais "
                "(planner → researcher → writer → critic). Mais lento, "
                "mais estruturado. Padrão usado por Devin e Agentforce."
            )
            with gr.Row():
                with gr.Column(scale=2):
                    m_input = gr.Textbox(
                        label="Sua pergunta",
                        placeholder=_EXAMPLE_PROMPTS[0],
                        lines=3,
                    )
                    m_button = gr.Button("Executar pipeline", variant="primary")
                with gr.Column(scale=3):
                    m_answer = gr.Textbox(
                        label="Resposta final",
                        lines=6,
                        interactive=False,
                    )

            gr.Markdown("### Trace dos 4 nós")
            with gr.Row():
                m_plan = gr.Textbox(label="1. PLAN", lines=4, interactive=False)
                m_context = gr.Textbox(label="2. CONTEXT", lines=4, interactive=False)
            with gr.Row():
                m_draft = gr.Textbox(label="3. DRAFT", lines=4, interactive=False)
                m_critique = gr.Textbox(label="4. CRITIQUE", lines=4, interactive=False)

            m_button.click(
                fn=handle_multi,
                inputs=m_input,
                outputs=[m_answer, m_plan, m_context, m_draft, m_critique],
            )

    gr.Markdown(
        """
        ---
        Engenharia de IA · Prof. Sergio Gaiotto · 2026.
        Código completo em [GitHub](https://github.com/) · Model Card em `docs/MODEL_CARD_v4.md`.
        """
    )


# Entry point do Space — HF chama assim
if __name__ == "__main__":
    demo.queue()  # habilita fila para múltiplos usuários simultâneos
    demo.launch(theme=gr.themes.Soft())
