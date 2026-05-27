"""Tool: gera prompts How Might We (HMW) estruturados.

Útil na fase Idear: transforma um problema bruto em N prompts de brainstorm.
"""


def run_ideation_prompt_generator(problem: str, count: int = 5) -> str:
    """Gera 'count' prompts HMW a partir de uma descrição de problema."""
    count = max(3, min(count, 10))

    templates = [
        "Como podemos {p} sem aumentar custos?",
        "Como podemos {p} em menos de uma semana?",
        "Como podemos {p} envolvendo o cliente desde o início?",
        "Como podemos {p} usando recursos que já temos?",
        "Como podemos {p} de forma que clientes recomendem a amigos?",
        "Como podemos {p} mantendo a identidade da marca?",
        "Como podemos {p} sem depender de tecnologia cara?",
        "Como podemos {p} aprendendo com concorrentes diretos?",
        "Como podemos {p} criando uma experiência memorável?",
        "Como podemos {p} reduzindo o esforço do cliente?",
    ]

    selected = templates[:count]
    p_norm = problem.strip().rstrip(".").lower()
    prompts = [t.format(p=p_norm) for t in selected]

    out = [
        f"Problema base: {problem.strip()}",
        f"\n{count} prompts HMW para brainstorm:",
    ]
    out.extend(f"  {i}. {prompt}" for i, prompt in enumerate(prompts, 1))
    out.append("\nRegra: gere pelo menos 5 ideias para cada prompt antes de avaliar.")
    return "\n".join(out)


ideation_prompt_generator_tool: dict = {
    "type": "function",
    "function": {
        "name": "ideation_prompt_generator",
        "description": (
            "Gera prompts How Might We (HMW) estruturados para sessão de "
            "brainstorm. Use na fase Idear do Design Thinking, depois de já "
            "ter um problema bem definido pela fase Definir."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "problem": {
                    "type": "string",
                    "description": "Problema definido na fase 2. Ex: 'reter clientes recorrentes'",
                },
                "count": {
                    "type": "integer",
                    "description": "Quantos prompts HMW gerar (3-10, padrão: 5)",
                    "default": 5,
                },
            },
            "required": ["problem"],
            "additionalProperties": False,
        },
    },
}
