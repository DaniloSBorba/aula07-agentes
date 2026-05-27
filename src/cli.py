"""CLI principal da aula. Wrapper Typer sobre todos os entry points.

Comandos:
  smoke  → testa OpenAI key + imports
  demo   → roda um exemplo simples do agente single
  ask    → faz uma pergunta ao agente single
  multi  → roda o agente multi LangGraph
  serve  → inicia FastAPI
  mcp    → inicia servidor MCP local
  eval   → roda avaliação BFCL local
"""
from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
app = typer.Typer(help="Aula 07 · CLI dos agentes")


@app.command()
def smoke() -> None:
    """Smoke test: imports + chave OpenAI + chamada nano de 1 token."""
    console.print(Panel.fit("Smoke test", style="cyan"))

    # 1. imports
    try:
        import langgraph  # noqa: F401
        import openai  # noqa: F401
        from fastapi import FastAPI  # noqa: F401

        console.print("  [green]✓[/green] imports OK")
    except ImportError as exc:
        console.print(f"  [red]✗[/red] import falhou: {exc}")
        raise typer.Exit(1) from exc

    # 2. settings
    try:
        from src.config import get_product_config, get_settings

        settings = get_settings()
        product = get_product_config()
        console.print(f"  [green]✓[/green] produto ativo: {product['name']}")
        console.print(f"  [green]✓[/green] modelo: {settings.openai_model}")
    except Exception as exc:  # noqa: BLE001
        console.print(f"  [red]✗[/red] config falhou: {exc}")
        raise typer.Exit(1) from exc

    # 3. chamada nano
    try:
        from src.llm import chat_completion

        msg = chat_completion(
            messages=[{"role": "user", "content": "Responda só com a palavra: pong"}],
            model="gpt-4.1-nano",
            temperature=0,
        )
        content = (msg.get("content") or "").strip()
        if "pong" in content.lower():
            console.print(f"  [green]✓[/green] OpenAI respondeu: '{content}'")
        else:
            console.print(f"  [yellow]?[/yellow] OpenAI respondeu (inesperado): '{content}'")
    except Exception as exc:  # noqa: BLE001
        console.print(f"  [red]✗[/red] chamada OpenAI falhou: {exc}")
        raise typer.Exit(1) from exc

    console.print(Panel.fit("[bold green]Smoke test OK[/bold green]"))


@app.command()
def demo() -> None:
    """Roda um exemplo simples (primeira pergunta do products.yaml)."""
    from src.agents.single_agent import SingleAgent
    from src.config import get_product_config

    config = get_product_config()
    query = config["example_prompts"][0]

    console.print(Panel.fit(f"Demo · {config['name']}", style="cyan"))
    console.print(f"[bold]Pergunta:[/bold] {query}\n")

    agent = SingleAgent(product_config=config)
    result = agent.run(query, verbose=False)

    _print_run_table(result)


@app.command()
def ask(query: str = typer.Argument(..., help="Pergunta para o agente")) -> None:
    """Faz uma pergunta ao agente single ReAct."""
    from src.agents.single_agent import SingleAgent

    console.print(Panel.fit(f"Pergunta: {query}", style="cyan"))
    agent = SingleAgent()
    result = agent.run(query, verbose=False)
    _print_run_table(result)


@app.command()
def multi(query: str = typer.Argument(..., help="Pergunta para o agente multi")) -> None:
    """Roda o agente multi (LangGraph: planner → researcher → writer → critic)."""
    from src.agents.multi_agent import run_multi_agent

    console.print(Panel.fit(f"Multi-agente · Pergunta: {query}", style="cyan"))
    state = run_multi_agent(query)

    console.print(Panel(state.get("plan", ""), title="1. PLAN", style="blue"))
    console.print(
        Panel((state.get("context", "")[:800] + "..."), title="2. CONTEXT", style="magenta")
    )
    console.print(Panel(state.get("draft_answer", ""), title="3. DRAFT", style="yellow"))
    console.print(Panel(state.get("critique", ""), title="4. CRITIQUE", style="red"))
    console.print(
        Panel.fit(state.get("final_answer", state.get("draft_answer", "")),
                  title="RESPOSTA FINAL", style="green")
    )


@app.command()
def serve() -> None:
    """Inicia o FastAPI em 0.0.0.0:8000."""
    import uvicorn

    from src.config import get_settings

    settings = get_settings()
    console.print(f"[cyan]Iniciando API em http://{settings.api_host}:{settings.api_port}[/cyan]")
    uvicorn.run("src.api.app:app", host=settings.api_host, port=settings.api_port, reload=False)


@app.command()
def mcp() -> None:
    """Inicia o servidor MCP local mock."""
    import uvicorn

    from src.config import get_settings

    settings = get_settings()
    console.print(f"[cyan]Iniciando MCP em http://{settings.mcp_host}:{settings.mcp_port}[/cyan]")
    uvicorn.run("src.mcp.server:app", host=settings.mcp_host, port=settings.mcp_port, reload=False)


@app.command()
def eval() -> None:
    """Roda avaliação BFCL local."""
    from evals.run_bfcl import run as run_bfcl

    run_bfcl()


def _print_run_table(result) -> None:
    """Pretty print do AgentRun."""
    table = Table(title="Trace do agente")
    table.add_column("Passo", style="cyan", width=6)
    table.add_column("Tipo", style="magenta", width=10)
    table.add_column("Detalhe", style="white")

    for step in result.steps:
        if step.is_final:
            table.add_row(str(step.step_number), "FINAL", step.final_answer[:300] or "")
        else:
            detail = f"tool={step.tool_name} args={step.tool_args}\n  result={(step.tool_result or '')[:200]}"
            table.add_row(str(step.step_number), "TOOL", detail)
    console.print(table)
    console.print(Panel.fit(result.final_answer, title="Resposta final", style="green"))


if __name__ == "__main__":
    app()
