# Aula 07 · Agentes de IA

> Engenharia de IA · Prof. Sergio Gaiotto · 2026

**Encerramento do curso.** Repositório completo com agente single ReAct, multi-agente em LangGraph, servidor MCP local, API FastAPI, avaliação BFCL e CI. Aluno escolhe entre dois produtos via uma única variável de ambiente.

## Quick start (Codespaces)

1. **Abra este repo no GitHub** → botão verde **Code** → aba **Codespaces** → **Create codespace on main**.
2. Espere 60-90 segundos. O devcontainer instala tudo sozinho.
3. Edite `.env` e coloque sua `OPENAI_API_KEY`.
4. No terminal:

   ```bash
   make smoke      # valida chave + imports
   make demo       # roda agente single ReAct em pergunta de exemplo
   ```

5. Para servir a API:

   ```bash
   make serve      # FastAPI em http://localhost:8000
   ```

## Escolha de produto

Edite `.env` e ajuste a variável:

```env
PRODUCT=educiacao     # tutor pedagógico (EducIAção)
# PRODUCT=designmind  # facilitador de Design Thinking (DesignMind AI)
```

Isso carrega persona, tools e knowledge base específicas do produto via `config/products.yaml`.

## Estrutura

```
aula07-agentes/
├── .devcontainer/              # Config Codespaces
├── .github/workflows/ci.yml    # CI: lint + tests offline
├── config/products.yaml        # 2 produtos (persona, tools, KB)
├── src/
│   ├── cli.py                  # CLI Typer (make smoke, demo, ask, ...)
│   ├── config.py               # Settings + product config
│   ├── llm.py                  # Cliente OpenAI compartilhado
│   ├── tools/                  # 5 tools: calculator, KB, classifiers, etc.
│   ├── agents/
│   │   ├── single_agent.py     # ReAct loop com OpenAI tools
│   │   └── multi_agent.py      # LangGraph: planner→researcher→writer→critic
│   ├── mcp/server.py           # MCP server local mock (porta 8001)
│   └── api/app.py              # FastAPI (porta 8000)
├── evals/
│   ├── datasets/bfcl_ptbr_subset.jsonl   # 10 casos PT-BR
│   └── run_bfcl.py             # Runner BFCL local
├── tests/                       # pytest offline
├── docs/
│   ├── MODEL_CARD_v4.md        # Model Card consolidado v1+v2+v3+v4
│   └── ARCHITECTURE.md         # Diagrama e decisões
└── Makefile                     # make help para ver tudo
```

## Comandos disponíveis

```bash
make help       # lista todos os comandos
make smoke      # smoke test (1 chamada nano à OpenAI)
make demo       # exemplo do agente single ReAct
make ask QUERY="sua pergunta"   # CLI direto
make multi QUERY="..."          # roda multi-agente LangGraph
make serve      # FastAPI em 8000
make mcp        # MCP server em 8001
make eval       # BFCL local (10 casos do produto)
make test       # pytest offline
make lint       # ruff
```

## Endpoints da API

Depois de `make serve`:

| Endpoint | Método | Descrição |
|---|---|---|
| `/` | GET | Info do serviço |
| `/health` | GET | Healthcheck |
| `/product` | GET | Config do produto ativo |
| `/agent/single` | POST | Roda agente single ReAct |
| `/agent/multi` | POST | Roda agente multi LangGraph |

**Documentação interativa**: http://localhost:8000/docs

Exemplo de chamada:

```bash
curl -X POST http://localhost:8000/agent/single \
  -H "Content-Type: application/json" \
  -d '{"query": "Como dividir 3/4 por 2/5?"}'
```

## Avaliação BFCL local

`make eval` roda 5 casos do seu produto e avalia 3 dimensões:

- **Tool selection** — o agente escolheu a tool correta?
- **Tool args** — passou argumentos sensatos?
- **Answer quality** — resposta contém termos esperados?

Resultados salvos em `results/bfcl_<produto>_<timestamp>.jsonl`.

Faixa esperada: **8/10 a 10/10 passes**. Abaixo de 7 indica problema na persona ou tools.

## Custo estimado por aluno

| Operação | Custo |
|---|---|
| Smoke test | < USD 0.001 |
| Demo (1 query) | ~USD 0.01 |
| Multi-agente (4 nós × 1 query) | ~USD 0.04 |
| Avaliação BFCL (5 casos) | ~USD 0.10 |
| Sessão de desenvolvimento (30 queries) | ~USD 0.50 |
| **Total típico da aula** | **~USD 1.00** |

Saldo mínimo recomendado na conta OpenAI: **USD 5**.

## Entregáveis da aula

1. Branch `aula07-agentes` no GitHub com tag `aula07-final`.
2. Model Card v4 atualizado em `docs/MODEL_CARD_v4.md`.
3. `make eval` passando com ≥ 7/10 no produto escolhido.
4. README do aluno descrevendo escolhas próprias (em `docs/MEU_AGENTE.md`).
5. **Deploy público em Hugging Face Spaces** com Gradio UI (instruções em `deploy/README_SPACE.md`).

## Deploy para produção (Hugging Face Spaces)

A pasta `deploy/` contém tudo para publicar seu agente como Space público gratuito:

- `app.py` · entry point Gradio com 2 abas (single e multi)
- `requirements.txt` · subset enxuto (sem dev tools, sem FastAPI)
- `README_SPACE.md` · guia passo a passo de publicação

Resumo: criar Space na UI HF → configurar Secret `OPENAI_API_KEY` → git push da pasta `deploy/` + `src/` + `config/`. Agente fica público em ~5 minutos.

Limitações conhecidas do Space gratuito (timeout 30s, sem auth, sem persistência) estão documentadas no `deploy/README_SPACE.md`.

## Continuidade do curso

Esta é a aula de **encerramento**. O pipeline aqui consolidado integra tudo:

- **Aulas 01-03** · escolha de modelo, prompts, eval
- **Aula 04** · golden dataset e juiz LLM
- **Aula 05** · RAG (knowledge_base_query é a versão simplificada disso)
- **Aula 06** · adapter LoRA (documentado no Model Card, não usado como motor)
- **Aula 07** · este repositório, encerramento prático

## Licença

Material didático. Uso livre para estudo. Citação ao autor obrigatória em derivados.
