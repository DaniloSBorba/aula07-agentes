"""Pipeline multi-agente em LangGraph.

Quatro nós em sequência condicional:

  [planner] → [researcher] → [writer] → [critic]
                                            ↓
                            (revisar) ← ← ← (refazer)

- planner: decompõe a pergunta em sub-tarefas
- researcher: usa tools para coletar contexto factual
- writer: redige resposta final usando o contexto
- critic: avalia se a resposta atende, decide se refaz ou aprova

Este é o padrão "plan-and-execute com self-critique" que aparece em
sistemas de produção como Devin, Cursor agents, Salesforce Agentforce.
"""
import json
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from src.config import get_product_config, get_settings
from src.llm import chat_completion
from src.tools import execute_tool, get_tools_for_product


# =============================================================================
# Estado compartilhado entre os nós
# =============================================================================
class GraphState(TypedDict):
    """Estado que flui entre todos os nós do grafo."""

    user_query: str
    plan: str
    context: str
    draft_answer: str
    critique: str
    final_answer: str
    iteration: int
    max_iterations: int
    messages: Annotated[list[dict], add_messages]


# =============================================================================
# Nó 1: Planner
# =============================================================================
def planner_node(state: GraphState) -> dict:
    """Decompõe a pergunta em 2-4 sub-tarefas concretas."""
    config = get_product_config()
    system = (
        f"Você é o PLANNER do agente {config['name']}. "
        "Sua função: receber uma pergunta do usuário e decompor em "
        "2 a 4 sub-tarefas concretas para o agente RESEARCHER executar. "
        "Saída: lista numerada, ATÔMICA, em português. "
        "NÃO responda a pergunta. Apenas planeje."
    )
    msg = chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": state["user_query"]},
        ],
        temperature=0.3,
    )
    plan = msg.get("content") or "1. Responder diretamente."
    return {"plan": plan}


# =============================================================================
# Nó 2: Researcher (usa tools)
# =============================================================================
def researcher_node(state: GraphState) -> dict:
    """Executa o plano usando as tools disponíveis para coletar contexto."""
    config = get_product_config()
    tools = get_tools_for_product(config)

    system = (
        f"Você é o RESEARCHER do agente {config['name']}. "
        "Você recebeu um PLANO de sub-tarefas. Para cada sub-tarefa, "
        "decida se precisa chamar uma tool. Chame tools quando precisar "
        "de fato verificável. NÃO redija a resposta final — apenas colete "
        "o CONTEXTO factual relevante para o WRITER usar depois. "
        "Quando terminar de pesquisar, responda em texto livre resumindo "
        "tudo que você descobriu."
    )

    messages: list[dict] = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"PERGUNTA ORIGINAL DO USUÁRIO:\n{state['user_query']}\n\n"
                f"PLANO:\n{state['plan']}\n\n"
                "Execute o plano usando tools quando necessário."
            ),
        },
    ]

    # Loop de tools até research final
    max_tool_iterations = 5
    for _ in range(max_tool_iterations):
        msg = chat_completion(
            messages=messages,
            tools=tools if tools else None,
            temperature=0.3,
        )
        messages.append(msg)
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            break
        for tool_call in tool_calls:
            fn = tool_call["function"]
            tool_name = fn["name"]
            try:
                tool_args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                tool_args = {}
            result = execute_tool(tool_name, tool_args)
            messages.append(
                {"role": "tool", "tool_call_id": tool_call["id"], "content": result}
            )

    # Último msg é o contexto coletado
    context = (messages[-1].get("content") if messages else "") or ""
    return {"context": context}


# =============================================================================
# Nó 3: Writer
# =============================================================================
def writer_node(state: GraphState) -> dict:
    """Redige a resposta final ao usuário usando o contexto coletado."""
    config = get_product_config()
    system = (
        f"{config['persona']}\n\n"
        "Você está na função WRITER deste sistema multi-agente. "
        "Use o CONTEXTO fornecido para redigir a resposta final ao usuário. "
        "Tom: conforme a persona acima. Não invente fatos que não estejam "
        "no contexto. Se algo está faltando, diga claramente."
    )
    user = (
        f"PERGUNTA DO USUÁRIO:\n{state['user_query']}\n\n"
        f"CONTEXTO COLETADO PELO RESEARCHER:\n{state['context']}\n\n"
    )
    if state.get("critique") and state.get("iteration", 0) > 0:
        user += (
            f"\nCRÍTICA DA VERSÃO ANTERIOR:\n{state['critique']}\n\n"
            "Refaça incorporando os pontos da crítica."
        )

    msg = chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.6,
    )
    draft = msg.get("content") or ""
    return {"draft_answer": draft}


# =============================================================================
# Nó 4: Critic
# =============================================================================
def critic_node(state: GraphState) -> dict:
    """Avalia a draft. Decide aprovar ou pedir refação."""
    config = get_product_config()
    system = (
        f"Você é o CRITIC do agente {config['name']}. "
        "Sua função: avaliar se a DRAFT atende à pergunta do usuário de "
        "forma completa, factualmente correta (à luz do CONTEXTO), e "
        "no tom da persona. Devolva JSON com duas chaves: "
        '"verdict" (uma string: "APROVADO" ou "REFAZER") e "feedback" '
        "(uma string em PT-BR explicando o motivo). "
        "Seja RIGOROSO mas justo: aprove quando estiver bom. NÃO peça "
        "refação para detalhes cosméticos."
    )
    user = (
        f"PERGUNTA:\n{state['user_query']}\n\n"
        f"CONTEXTO:\n{state['context']}\n\n"
        f"DRAFT:\n{state['draft_answer']}\n"
    )
    msg = chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    raw = msg.get("content") or '{"verdict":"APROVADO","feedback":"ok"}'
    try:
        parsed = json.loads(raw)
        critique = parsed.get("feedback", "")
        verdict = parsed.get("verdict", "APROVADO").upper()
    except json.JSONDecodeError:
        critique = raw
        verdict = "APROVADO"

    new_iteration = state.get("iteration", 0) + 1

    # Se atingiu max ou aprovou: promove draft para final
    if verdict == "APROVADO" or new_iteration >= state.get("max_iterations", 2):
        return {
            "critique": critique,
            "iteration": new_iteration,
            "final_answer": state["draft_answer"],
        }

    return {"critique": critique, "iteration": new_iteration}


# =============================================================================
# Roteamento condicional
# =============================================================================
def should_continue(state: GraphState) -> Literal["writer", "end"]:
    """Decide se volta ao writer (refazer) ou termina."""
    if state.get("final_answer"):
        return "end"
    return "writer"


# =============================================================================
# Construtor do grafo
# =============================================================================
def build_graph():
    """Constrói o StateGraph LangGraph com os 4 nós e o ciclo de revisão."""
    graph = StateGraph(GraphState)

    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("writer", writer_node)
    graph.add_node("critic", critic_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "writer")
    graph.add_edge("writer", "critic")
    graph.add_conditional_edges(
        "critic",
        should_continue,
        {"writer": "writer", "end": END},
    )

    return graph.compile()


# =============================================================================
# Entry point conveniente
# =============================================================================
def run_multi_agent(user_query: str, max_iterations: int = 2) -> dict:
    """Roda o pipeline e retorna estado final."""
    app = build_graph()
    initial_state: GraphState = {
        "user_query": user_query,
        "plan": "",
        "context": "",
        "draft_answer": "",
        "critique": "",
        "final_answer": "",
        "iteration": 0,
        "max_iterations": max_iterations,
        "messages": [],
    }
    final_state = app.invoke(initial_state)
    return final_state
