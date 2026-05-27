.PHONY: help install smoke test eval serve mcp clean format lint demo

# Variáveis carregadas do .env quando rodadas via cli interno
PYTHON := python

help:  ## Mostra todos os comandos disponíveis
	@echo "============================================================"
	@echo "  Aula 07 · Agentes de IA · Comandos disponíveis"
	@echo "============================================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'
	@echo ""

install:  ## Instala dependências (já feito no setup do Codespace)
	pip install -e ".[dev]"

smoke:  ## Smoke test rápido (verifica chave OpenAI e imports)
	$(PYTHON) -m src.cli smoke

demo:  ## Roda um exemplo simples do agente smolagents
	$(PYTHON) -m src.cli demo

serve:  ## Inicia FastAPI em http://localhost:8000
	$(PYTHON) -m src.cli serve

mcp:  ## Inicia servidor MCP local mock em http://localhost:8001
	$(PYTHON) -m src.cli mcp

ask:  ## Pergunta ao agente via CLI. Uso: make ask QUERY="sua pergunta"
	$(PYTHON) -m src.cli ask "$(QUERY)"

eval:  ## Roda avaliação BFCL local (function calling em PT-BR)
	$(PYTHON) -m src.cli eval

gradio:  ## Roda Gradio UI localmente (mesma UI do HF Space) em :7860
	$(PYTHON) deploy/app.py

test:  ## Roda suite de testes pytest
	pytest

format:  ## Formata código com ruff
	ruff format src tests evals

lint:  ## Verifica qualidade do código com ruff
	ruff check src tests evals

clean:  ## Remove arquivos temporários
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf build/ dist/ *.egg-info/

all-checks: lint test smoke  ## Roda lint + testes + smoke (CI local)
