"""Registry de ferramentas disponíveis para os agentes.

Cada tool é uma função pura com docstring e type hints.
A função `get_tools_for_product` retorna o subset configurado no products.yaml.
"""
from src.tools.calculator import calculator_tool, run_calculator
from src.tools.design_validator import design_phase_validator_tool, run_design_phase_validator
from src.tools.grade_classifier import grade_level_classifier_tool, run_grade_level_classifier
from src.tools.ideation_generator import (
    ideation_prompt_generator_tool,
    run_ideation_prompt_generator,
)
from src.tools.knowledge_base import knowledge_base_query_tool, run_knowledge_base_query

# Mapeamento nome → (schema OpenAI, função executora)
TOOL_REGISTRY: dict[str, tuple[dict, callable]] = {
    "calculator": (calculator_tool, run_calculator),
    "knowledge_base_query": (knowledge_base_query_tool, run_knowledge_base_query),
    "grade_level_classifier": (grade_level_classifier_tool, run_grade_level_classifier),
    "design_phase_validator": (design_phase_validator_tool, run_design_phase_validator),
    "ideation_prompt_generator": (ideation_prompt_generator_tool, run_ideation_prompt_generator),
}


def get_tools_for_product(product_config: dict) -> list[dict]:
    """Retorna os schemas OpenAI das tools habilitadas para o produto."""
    enabled = product_config.get("tools", [])
    schemas = []
    for tool_name in enabled:
        if tool_name not in TOOL_REGISTRY:
            raise ValueError(f"Tool '{tool_name}' não está no registry.")
        schema, _ = TOOL_REGISTRY[tool_name]
        schemas.append(schema)
    return schemas


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Executa uma tool pelo nome com os argumentos fornecidos.

    Retorna sempre string (formato esperado pelo OpenAI tool_result).
    """
    if tool_name not in TOOL_REGISTRY:
        return f"ERRO: tool '{tool_name}' não existe. Tools disponíveis: {list(TOOL_REGISTRY)}"
    _, fn = TOOL_REGISTRY[tool_name]
    try:
        return fn(**arguments)
    except Exception as exc:  # noqa: BLE001
        return f"ERRO ao executar '{tool_name}': {exc}"
