# Architecture · Aula 07

Diagrama da estrutura runtime e decisões de design.

## Visão de runtime

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Codespaces                       │
│                                                                 │
│  ┌──────────────┐                            ┌─────────────┐    │
│  │   CLI/User   │ ◄──── http :8000 ────────► │  FastAPI    │    │
│  └──────────────┘                            │  /agent/*   │    │
│                                              └──────┬──────┘    │
│                                                     │           │
│                              ┌──────────────────────┴─────┐     │
│                              │                            │     │
│                      ┌───────▼────────┐         ┌─────────▼──┐  │
│                      │ SingleAgent    │         │ MultiAgent │  │
│                      │ (ReAct loop)   │         │ LangGraph  │  │
│                      └───────┬────────┘         └─────┬──────┘  │
│                              │                        │         │
│                              ▼                        ▼         │
│                      ┌───────────────────────────────────┐     │
│                      │       TOOL_REGISTRY (src/tools)   │     │
│                      │  calculator, KB, classifiers...   │     │
│                      └─────────────────┬─────────────────┘     │
│                                        │                       │
│                              ┌─────────▼─────────┐             │
│                              │  OpenAI API       │             │
│                              │  gpt-4.1-mini     │             │
│                              └───────────────────┘             │
│                                                                 │
│  ┌─────────────────────────┐                                   │
│  │ MCP Server (porta 8001) │ ◄─── opcional, didático           │
│  │ list_tools / call_tool  │                                   │
│  └─────────────────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Fluxo Single ReAct

```
user_query
   │
   ▼
 [LLM] ──tool_calls?──► YES → execute_tool() → tool_result ──┐
   │                                                          │
   │ NO                                                       │
   ▼                                                          │
final_answer ◄──────────────────────────────────────────── loop
```

Limite: 8 iterações.

## Fluxo Multi LangGraph

```
   user_query
       │
       ▼
   ┌───────────┐
   │  PLANNER  │ ─► plan: "1. ... 2. ... 3. ..."
   └─────┬─────┘
         │
         ▼
   ┌────────────┐
   │ RESEARCHER │ ─► context (via tools)
   └─────┬──────┘     loop interno até research final
         │            (max 5 chamadas de tool)
         ▼
   ┌─────────┐
   │ WRITER  │ ─► draft_answer
   └────┬────┘
        │
        ▼
   ┌─────────┐
   │ CRITIC  │ ─► JSON {verdict, feedback}
   └────┬────┘
        │
        ├── verdict=APROVADO ──► final_answer = draft ──► END
        │
        └── verdict=REFAZER ──► volta para WRITER
                                (até max_iterations=2)
```

## Decisões de design

| Decisão | Alternativa rejeitada | Por quê |
|---|---|---|
| OpenAI tools nativo no single, sem smolagents | smolagents | Menos uma camada de abstração; código didático |
| LangGraph para multi | CrewAI | LangGraph venceu em adoção 2025-2026 |
| `gpt-4.1-mini` padrão | `gpt-4.1` | Custo 8× menor, function calling pareia em qualidade |
| Knowledge base por palavras-chave | Embeddings/RAG completo | Aula 07 ensina agentes, não retrieval |
| MCP local mock | Conectores reais | Não exige credenciais externas em sala |
| Devcontainer Codespaces | Colab | Multi-arquivo, terminal, git nativo |
| pydantic-settings para config | Variáveis crus | Validação cedo, falha clara |
| Typer para CLI | Click direto | Type hints e help automático |

## Custos

| Camada | Custo aprox. por aluno |
|---|---|
| Codespaces Free | 60h/mês inclusas |
| OpenAI API | ~USD 1.00 sessão completa |
| GitHub Actions CI | 2000 min/mês free |
| **Total** | **~USD 1.00** |

## Trade-offs explicitamente aceitos

1. **Sem memória de longo prazo.** Cada chamada é independente. Aceitável para uma aula; em produção, adicionar Redis.
2. **MCP é mock.** Não roda stdio nem SSE. Ensina o padrão de chamada, não a infraestrutura.
3. **BFCL com 5 casos.** Demonstra a metodologia. Em produção, expandir.
4. **Critic pode aprovar respostas medianas.** Modelo é juiz tendencioso a aprovar. Em produção, juiz humano periódico.
