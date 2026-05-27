"""Tool: consulta à base de conhecimento do produto ativo.

Implementação simples por palavras-chave (TF-IDF leve em memória).
Em produção, isso seria substituído por RAG real (Aula 05).
Aqui o objetivo é ensinar o PADRÃO de tool de busca, não a engine de busca.
"""
import re
from typing import Iterable

from src.config import get_product_config


def _stem(token: str) -> str:
    """Stemming português curto para casar singular/plural.

    Casos cobertos:
      frações  → fraç     fração   → fraç
      equações → equaç    equação  → equaç
      ideias   → idei     ideia    → idei
      cliente  → client   clientes → client
    """
    if len(token) > 4 and (token.endswith("ções") or token.endswith("ões")):
        # frações → fraç ; equações → equaç ; reflexões → reflex
        return token[:-4] if token.endswith("ções") else token[:-3]
    if len(token) > 4 and (token.endswith("ção") or token.endswith("ão")):
        return token[:-3] if token.endswith("ção") else token[:-2]
    if len(token) > 4 and token.endswith("es"):
        return token[:-2]
    if len(token) > 3 and token.endswith("s"):
        return token[:-1]
    if len(token) > 3 and token.endswith("a"):
        # ideia → idei ; idéia → idéi
        return token[:-1]
    return token


def _tokenize(text: str) -> list[str]:
    """Tokeniza: minúsculo, remove pontuação, splita, stemiza por aproximação."""
    text = text.lower()
    text = re.sub(r"[^\w\sáéíóúâêôãõàç]", " ", text)
    return [_stem(t) for t in text.split() if len(t) >= 3]


def _score(query_tokens: Iterable[str], doc_tokens: Iterable[str]) -> int:
    """Score = quantidade de tokens stemizados da query presentes no doc."""
    doc_set = set(doc_tokens)
    return sum(1 for t in query_tokens if t in doc_set)


def run_knowledge_base_query(query: str, top_k: int = 2) -> str:
    """Busca os top_k documentos mais relevantes da KB do produto ativo."""
    config = get_product_config()
    kb = config.get("knowledge_base", [])
    if not kb:
        return "Base de conhecimento vazia para este produto."

    query_tokens = _tokenize(query)

    scored: list[tuple[int, dict]] = []
    for doc in kb:
        all_text = f"{doc['title']} {doc['content']}"
        doc_tokens = _tokenize(all_text)
        score = _score(query_tokens, doc_tokens)
        scored.append((score, doc))

    # Ordena por score desc, mantém só os com score > 0
    scored = sorted(scored, key=lambda x: x[0], reverse=True)
    relevant = [doc for score, doc in scored if score > 0][:top_k]

    if not relevant:
        return f"Nenhum documento relevante encontrado para a query: '{query}'"

    out_lines = [f"Encontrados {len(relevant)} documento(s):"]
    for i, doc in enumerate(relevant, 1):
        out_lines.append(f"\n--- Documento {i}: {doc['title']} ---")
        out_lines.append(doc["content"].strip())
    return "\n".join(out_lines)


knowledge_base_query_tool: dict = {
    "type": "function",
    "function": {
        "name": "knowledge_base_query",
        "description": (
            "Busca conteúdo na base de conhecimento curada do produto. "
            "Use SEMPRE que precisar de fato pedagógico (EducIAção) ou "
            "de orientação de fase de Design Thinking (DesignMind). "
            "NÃO invente conteúdo da KB — sempre busque primeiro."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Palavras-chave da busca. Exemplo: 'fração equivalente'",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Número de documentos a retornar (padrão: 2)",
                    "default": 2,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}
