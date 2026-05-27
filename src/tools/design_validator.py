"""Tool: identifica em qual fase de Design Thinking o usuário está.

Útil para o agente DesignMind saber se deve guiar o usuário a continuar
na fase atual ou avançar para a próxima.
"""

_PHASES: dict[str, list[str]] = {
    "empatizar": [
        "entender cliente", "entrevista", "pesquisa", "observar",
        "por que cliente", "feedback negativo", "queixa", "dor do usuário",
        "não sei o que clientes querem", "shadowing", "mapa de empatia",
    ],
    "definir": [
        "sintetizar", "padrão nos dados", "principal problema",
        "ponto de vista", "point of view", "como definir",
        "qual é o problema real", "insight",
    ],
    "idear": [
        "brainstorm", "ideias", "como gerar", "soluções possíveis",
        "how might we", "criatividade", "alternativas",
    ],
    "prototipar": [
        "protótipo", "mvp", "esboço", "mockup", "construir versão",
        "testar versão", "fazer rápido", "low fidelity",
    ],
    "testar": [
        "testar com cliente", "feedback do protótipo", "validar",
        "experimentar", "piloto", "usabilidade",
    ],
}


def run_design_phase_validator(user_description: str) -> str:
    """Identifica fase atual do DT e dá orientação curta sobre próximo passo."""
    text = user_description.lower()

    scores: dict[str, int] = {}
    for phase, keywords in _PHASES.items():
        scores[phase] = sum(1 for kw in keywords if kw in text)

    if all(v == 0 for v in scores.values()):
        return (
            "FASE: indefinida. Recomendação: pergunte ao usuário em qual fase "
            "ele está (empatizar, definir, idear, prototipar, testar) ou ajude "
            "a começar pela fase 1 (Empatizar)."
        )

    phase: str = max(scores, key=lambda k: scores[k])

    next_step: dict[str, str] = {
        "empatizar": "Próximo passo: realizar 5-7 entrevistas qualitativas com clientes reais.",
        "definir": "Próximo passo: usar formato Point of View [usuário] precisa de [necessidade] porque [insight].",
        "idear": "Próximo passo: aplicar How Might We — meta de 30+ ideias antes de filtrar.",
        "prototipar": "Próximo passo: construir protótipo descartável (storyboard, papel, mockup).",
        "testar": "Próximo passo: testar com 5-7 usuários, observe COMPORTAMENTO, não pergunte opinião.",
    }

    return f"FASE identificada: {phase.upper()}. {next_step[phase]}"


design_phase_validator_tool: dict = {
    "type": "function",
    "function": {
        "name": "design_phase_validator",
        "description": (
            "Identifica em qual das 5 fases de Design Thinking (Empatizar, "
            "Definir, Idear, Prototipar, Testar) o usuário está. Use SEMPRE "
            "no início da conversa para orientar a próxima ação."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "user_description": {
                    "type": "string",
                    "description": "Texto que o usuário enviou descrevendo onde está.",
                }
            },
            "required": ["user_description"],
            "additionalProperties": False,
        },
    },
}
