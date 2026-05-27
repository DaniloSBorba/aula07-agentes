"""Tool: classifica em qual nível escolar um conteúdo se encaixa.

Heurística simples baseada em palavras-chave do currículo BNCC.
Útil quando o aluno descreve um problema sem dizer a série.
"""
from typing import Literal

_KEYWORDS_FUNDAMENTAL_1: list[str] = [
    "soma", "subtração", "adição", "tabuada", "número natural",
    "alfabeto", "sílaba", "leitura", "primeiro ano", "segundo ano",
    "terceiro ano", "quarto ano", "quinto ano",
]
_KEYWORDS_FUNDAMENTAL_2: list[str] = [
    "fração", "decimal", "porcentagem", "regra de três", "mmc", "mdc",
    "área", "perímetro", "ângulo", "polígono", "sexto ano", "sétimo ano",
    "oitavo ano", "nono ano",
]
_KEYWORDS_MEDIO: list[str] = [
    "equação", "função", "logaritmo", "trigonometria", "matriz",
    "vetor", "bhaskara", "primeiro grau", "segundo grau", "geometria analítica",
    "ensino médio", "vestibular", "enem",
]


def run_grade_level_classifier(text: str) -> str:
    """Classifica em qual etapa da educação básica o tema se encaixa."""
    t = text.lower()

    def _count(keywords: list[str]) -> int:
        return sum(1 for kw in keywords if kw in t)

    scores = {
        "fundamental_anos_iniciais": _count(_KEYWORDS_FUNDAMENTAL_1),
        "fundamental_anos_finais": _count(_KEYWORDS_FUNDAMENTAL_2),
        "ensino_medio": _count(_KEYWORDS_MEDIO),
    }
    best: str = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return (
            "Não foi possível classificar com confiança. "
            "Sugestão: pedir ao aluno em qual série/ano ele está."
        )

    labels: dict[str, str] = {
        "fundamental_anos_iniciais": "Ensino Fundamental · Anos Iniciais (1º-5º)",
        "fundamental_anos_finais": "Ensino Fundamental · Anos Finais (6º-9º)",
        "ensino_medio": "Ensino Médio (1º-3º ano)",
    }
    return (
        f"Nível classificado: {labels[best]} "
        f"(score: {scores[best]} palavras-chave encontradas). "
        f"Adapte sua resposta para este nível."
    )


grade_level_classifier_tool: dict = {
    "type": "function",
    "function": {
        "name": "grade_level_classifier",
        "description": (
            "Classifica em qual etapa da educação básica brasileira (Fund. Iniciais, "
            "Fund. Finais, Ensino Médio) o conteúdo se encaixa. Use no INÍCIO da "
            "interação quando o aluno não especifica a série."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Texto a classificar (a pergunta do aluno ou tópico).",
                }
            },
            "required": ["text"],
            "additionalProperties": False,
        },
    },
}
