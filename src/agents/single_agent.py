"""Agente single ReAct usando OpenAI tools nativo.

Implementação minimalista e didática do padrão ReAct: o LLM raciocina,
decide qual tool chamar, recebe o resultado, e itera até produzir resposta final.

Esta implementação NÃO depende de smolagents (que adiciona uma camada de
abstração e dependências pesadas). Aqui usamos diretamente o SDK OpenAI,
o que torna o código mais fácil de auditar e ensinar.
"""
import json
from dataclasses import dataclass, field
from typing import Any

from src.config import get_product_config, get_settings
from src.llm import chat_completion
from src.tools import execute_tool, get_tools_for_product


@dataclass
class AgentStep:
    """Um passo do loop ReAct."""

    step_number: int
    thought: str | None = None
    tool_name: str | None = None
    tool_args: dict | None = None
    tool_result: str | None = None
    is_final: bool = False
    final_answer: str | None = None


@dataclass
class AgentRun:
    """Resultado de uma execução completa do agente."""

    user_query: str
    final_answer: str
    steps: list[AgentStep] = field(default_factory=list)
    total_tokens: int = 0


class SingleAgent:
    """Agente single ReAct com loop limitado.

    Limite de iterações evita loops infinitos quando o LLM não converge.
    """

    MAX_ITERATIONS = 8

    def __init__(self, product_config: dict | None = None):
        self.product_config: dict = product_config or get_product_config()
        self.settings = get_settings()
        self.system_prompt: str = self.product_config["persona"]
        self.tools: list[dict] = get_tools_for_product(self.product_config)

    def run(self, user_query: str, verbose: bool = False) -> AgentRun:
        """Executa o loop ReAct até resposta final ou MAX_ITERATIONS."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query},
        ]
        run = AgentRun(user_query=user_query, final_answer="")

        for i in range(1, self.MAX_ITERATIONS + 1):
            step = AgentStep(step_number=i)

            response_msg = chat_completion(
                messages=messages,
                tools=self.tools if self.tools else None,
                temperature=0.7,
            )

            # Acumula no histórico (formato OpenAI espera tool_calls intactas)
            messages.append(response_msg)

            tool_calls = response_msg.get("tool_calls") or []

            if not tool_calls:
                # Sem mais ferramentas → resposta final
                step.is_final = True
                step.final_answer = response_msg.get("content") or ""
                run.steps.append(step)
                run.final_answer = step.final_answer
                if verbose:
                    print(f"[passo {i}] FINAL: {step.final_answer[:200]}")
                break

            # Há chamadas de tools — execute cada uma e siga
            for tool_call in tool_calls:
                fn = tool_call["function"]
                tool_name = fn["name"]
                try:
                    tool_args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    tool_args = {}

                step.tool_name = tool_name
                step.tool_args = tool_args

                tool_result = execute_tool(tool_name, tool_args)
                step.tool_result = tool_result

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result,
                    }
                )

                if verbose:
                    print(f"[passo {i}] tool={tool_name} args={tool_args}")
                    print(f"[passo {i}] result={tool_result[:200]}")

            run.steps.append(step)

        if not run.final_answer:
            # MAX_ITERATIONS atingido sem resposta final
            run.final_answer = (
                "(O agente atingiu o limite de iterações sem produzir resposta final. "
                "Reformule sua pergunta de forma mais específica.)"
            )

        return run
