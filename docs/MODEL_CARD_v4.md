# Model Card v4 · Agente Final

> Documento consolidado · Engenharia de IA · Aula 07 (encerramento)
> Versões anteriores: v1 (Aula 03), v2 (Aula 05), v3 (Aula 06).
> Esta v4 consolida e marca o estado final do produto.

---

## Identificação

| Campo | Valor |
|---|---|
| **Produto** | (escolha entre EducIAção \| DesignMind AI) |
| **Versão** | 4.0 (encerramento) |
| **Data** | 2026-MM-DD |
| **Aluno** | (seu nome) |
| **Branch** | `aula07-agentes` |
| **Tag** | `aula07-final` |
| **Modelo base** | gpt-4.1-mini (orquestração do agente) |
| **Modelo do juiz** | gpt-4.1 (avaliação BFCL) |

---

## Camada A · Escolha de modelo (Aula 03)

[Preservar conteúdo original da v1. Não alterar.]

---

## Camada B · RAG (Aula 05)

[Preservar conteúdo original da v2. Não alterar.]

---

## Camada C · Fine-tuning LoRA (Aula 06)

[Preservar conteúdo original da v3. Não alterar.]

**Decisão sobre o adapter na Aula 07**: o adapter LoRA permanece arquivado em `MyDrive/aula06_finetune/adapter_v1/`. Não é usado como motor do agente. **Justificativa técnica**: function calling é capability emergente do pré-treinamento em larga escala — não é induzida por SFT em 250 exemplos. Usar o adapter como motor causaria chamadas de função mal-formadas. O adapter melhora estilo/tom em casos onde o modelo gera texto livre direto ao usuário, não onde o modelo precisa estruturar chamadas.

---

## Camada D · Agente final (Aula 07)

### D.1 · Arquitetura

Dois agentes coexistem no repositório, ambos servidos via FastAPI:

#### Agente single (ReAct)
```
[user] → LLM ⇄ [tools] → LLM → [resposta]
              ↑ loop até resposta final, max 8 iterações
```

Implementação: `src/agents/single_agent.py` · `SingleAgent.run()`.

Tools disponíveis no produto ativo (configuradas em `config/products.yaml`):

**EducIAção**:
- `calculator` · aritmética segura via AST
- `knowledge_base_query` · busca por palavras-chave na KB
- `grade_level_classifier` · BNCC: Fund. Iniciais / Finais / Médio

**DesignMind AI**:
- `design_phase_validator` · identifica fase DT (Empatizar→Testar)
- `knowledge_base_query` · busca na KB de Design Thinking
- `ideation_prompt_generator` · gera prompts HMW

#### Agente multi (LangGraph)
```
START → [planner] → [researcher] → [writer] → [critic]
                                                  ↓
                                  approve  ⊕  refazer
                                     ↓         ↓
                                    END     [writer]
```

Implementação: `src/agents/multi_agent.py` · `run_multi_agent()`.

Estado compartilhado: `GraphState` (TypedDict). Quatro nós:
- `planner_node` — decompõe pergunta em 2-4 sub-tarefas (temperature=0.3)
- `researcher_node` — executa plano com tools (temperature=0.3)
- `writer_node` — redige resposta usando contexto coletado (temperature=0.6)
- `critic_node` — JSON mode, devolve `{verdict, feedback}` (temperature=0.2)

Loop de revisão limitado por `max_iterations` (default: 2).

### D.2 · Protocolo MCP

Servidor MCP local mock em `src/mcp/server.py`. Expõe duas tools didáticas (`current_datetime`, `format_brazilian_currency`) via dois endpoints (`list_tools`, `call_tool`) compatíveis com o padrão MCP da Anthropic.

Propósito: ensinar o padrão de comunicação que conectores reais (GitHub, Slack, Filesystem) usam, sem depender de credenciais externas em sala.

### D.3 · Avaliação BFCL local

Dataset: `evals/datasets/bfcl_ptbr_subset.jsonl` — 10 casos PT-BR (5 por produto).

Três dimensões avaliadas:
| Dimensão | Pergunta | Como medir |
|---|---|---|
| Tool selection | O agente escolheu a tool correta? | `expected_tool in tools_used` |
| Tool args | Os argumentos passados são sensatos? | substring esperada presente |
| Answer quality | A resposta contém termos esperados? | qualquer termo de `expected_in_answer` |

**Resultado** (preencha após `make eval`):

| Dimensão | Score |
|---|---|
| Tool selection | __ / 5 |
| Tool args | __ / 5 |
| Answer quality | __ / 5 |
| **TOTAL pass** | __ / 5 |

### D.4 · Decisão de promoção a produção

Critério mecânico:

| BFCL pass rate | Decisão |
|---|---|
| ≥ 80% (4-5 de 5) | **Promover** para deploy |
| 60-79% (3 de 5) | **Iterar** persona ou tools |
| < 60% (≤ 2 de 5) | **Regressão** — investigar antes de tentar deploy |

**Sua decisão**: [PROMOVER \| ITERAR \| REGREDIR]

**Justificativa em 3 frases**: ___

---

## Limitações conhecidas

- **Knowledge base** é busca por palavras-chave, não embeddings. Em produção real, substituir por RAG vetorial (Aula 05).
- **Multi-agente** não tem persistência de memória entre conversas. Estado morre ao fim da chamada.
- **MCP local** é mock didático. Não implementa o protocolo MCP completo (stdio, SSE, oauth).
- **Avaliação BFCL** tem apenas 5 casos por produto. Score < 80% em amostra tão pequena pode ser ruído. Em produção, expandir para 50-200 casos.

## Riscos e mitigações

| Risco | Mitigação implementada | Mitigação faltante |
|---|---|---|
| Prompt injection via input do usuário | Persona forte separa sistema/usuário | Sanitização explícita |
| Loop infinito de tool calls | `MAX_ITERATIONS=8` no single | — |
| Custos descontrolados | Modelo padrão `gpt-4.1-mini`; saldo limita | Rate limiting na API |
| Vazamento de chave | `.env` no `.gitignore`; Secret no Codespaces | Rotação automática |
| Resposta factualmente errada | Critic node revisa antes de retornar | RAG real para citação |

## Próximos passos pós-curso

1. Deploy do agente como Space público no Hugging Face com Gradio UI.
2. Trocar `knowledge_base` simples pelo RAG vetorial da Aula 05.
3. Adicionar memória persistente (Redis ou Postgres) ao multi-agente.
4. Expandir BFCL de 5 para 50 casos por produto.
5. Implementar MCP server real (stdio) com tools de produção (DB, e-mail, calendário).

---

*Documento auditável. Última atualização: 2026-MM-DD.*
