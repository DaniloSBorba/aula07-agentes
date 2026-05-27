"""Runner do BFCL subset local (PT-BR).

Avalia o agente em três dimensões:

  1. Tool selection (escolheu a tool correta?)
  2. Tool args (passou argumentos sensatos?)
  3. Answer quality (resposta final contém termos esperados?)

Saída: tabela resumo + JSONL detalhado em results/.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from src.agents.single_agent import SingleAgent
from src.config import get_product_config, get_settings

console = Console()

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT / "evals" / "datasets" / "bfcl_ptbr_subset.jsonl"
RESULTS_DIR = ROOT / "results"


def load_cases(product: str) -> list[dict]:
    """Carrega os casos do dataset filtrando pelo produto ativo."""
    cases: list[dict] = []
    with DATASET_PATH.open(encoding="utf-8") as f:
        for line in f:
            case = json.loads(line)
            if case["product"] == product:
                cases.append(case)
    return cases


def evaluate_case(case: dict, agent: SingleAgent) -> dict:
    """Avalia um caso. Retorna dict com 3 booleans e detalhes."""
    result = agent.run(case["query"], verbose=False)

    # Pegar todos os tool calls dos steps
    tools_used: list[str] = [s.tool_name for s in result.steps if s.tool_name]
    args_concat: str = " ".join(
        json.dumps(s.tool_args or {}, ensure_ascii=False) for s in result.steps if s.tool_args
    )
    final = (result.final_answer or "").lower()

    # 1. Tool selection
    tool_ok = case["expected_tool"] in tools_used

    # 2. Tool args
    args_ok = case["expected_args_substring"].lower() in args_concat.lower()

    # 3. Answer contém algum termo esperado
    expected_terms = [t.lower() for t in case["expected_in_answer"]]
    answer_ok = any(term in final for term in expected_terms)

    return {
        "id": case["id"],
        "query": case["query"],
        "tools_used": tools_used,
        "expected_tool": case["expected_tool"],
        "tool_ok": tool_ok,
        "args_ok": args_ok,
        "answer_ok": answer_ok,
        "passed": tool_ok and args_ok and answer_ok,
        "final_answer": result.final_answer[:300],
    }


def run() -> dict:
    """Roda toda a avaliação e imprime resumo."""
    settings = get_settings()
    product = settings.product
    config = get_product_config()

    console.print(f"\n[bold cyan]BFCL Local · Produto: {config['name']}[/bold cyan]")
    cases = load_cases(product)
    if not cases:
        console.print(f"[red]Nenhum caso para o produto '{product}'.[/red]")
        return {}

    console.print(f"Avaliando {len(cases)} casos com modelo {settings.openai_model}...\n")

    agent = SingleAgent(product_config=config)
    results: list[dict] = []
    for i, case in enumerate(cases, 1):
        console.print(f"  [{i}/{len(cases)}] {case['id']}: {case['query'][:60]}...")
        results.append(evaluate_case(case, agent))

    # Resumo
    n_total = len(results)
    n_tool_ok = sum(1 for r in results if r["tool_ok"])
    n_args_ok = sum(1 for r in results if r["args_ok"])
    n_answer_ok = sum(1 for r in results if r["answer_ok"])
    n_passed = sum(1 for r in results if r["passed"])

    table = Table(title=f"Resumo BFCL · {product}")
    table.add_column("Dimensão", style="cyan")
    table.add_column("Score", style="white")
    table.add_column("%", style="green")
    table.add_row("Tool selection", f"{n_tool_ok}/{n_total}", f"{100*n_tool_ok/n_total:.0f}%")
    table.add_row("Tool args sensatos", f"{n_args_ok}/{n_total}", f"{100*n_args_ok/n_total:.0f}%")
    table.add_row("Answer quality", f"{n_answer_ok}/{n_total}", f"{100*n_answer_ok/n_total:.0f}%")
    table.add_row("[bold]TOTAL pass[/bold]", f"{n_passed}/{n_total}", f"[bold]{100*n_passed/n_total:.0f}%[/bold]")
    console.print(table)

    # Salvar resultados em JSONL
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"bfcl_{product}_{timestamp}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    console.print(f"\n[dim]Detalhes salvos em: {out_path}[/dim]")

    return {
        "product": product,
        "total": n_total,
        "tool_ok": n_tool_ok,
        "args_ok": n_args_ok,
        "answer_ok": n_answer_ok,
        "passed": n_passed,
    }


if __name__ == "__main__":
    run()
