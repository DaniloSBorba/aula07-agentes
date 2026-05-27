"""Servidor MCP local (mock).

Implementação minimalista do protocolo MCP (Model Context Protocol) da
Anthropic. NÃO é uma implementação completa do spec — é didática.

Expõe duas tools via endpoints HTTP:
  POST /mcp/list_tools  → lista das tools disponíveis (schema)
  POST /mcp/call_tool   → executa uma tool e retorna resultado

O aluno aprende como um agente comunicaria com servidor MCP REAL
(GitHub, Slack, Filesystem, etc.) usando o mesmo padrão de chamada.

Rode com: make mcp (escuta em 127.0.0.1:8001)
"""
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Aula 07 · MCP Local Mock",
    description="Servidor MCP didático com 2 tools de exemplo.",
    version="1.0.0",
)


# =============================================================================
# Tools disponíveis no MCP local
# =============================================================================
MCP_TOOLS = {
    "current_datetime": {
        "name": "current_datetime",
        "description": "Retorna data e hora atuais em UTC e horário de Brasília.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    "format_brazilian_currency": {
        "name": "format_brazilian_currency",
        "description": "Formata um número como moeda brasileira (R$).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number", "description": "Valor numérico"},
            },
            "required": ["amount"],
        },
    },
}


# =============================================================================
# Implementações das tools
# =============================================================================
def _impl_current_datetime() -> dict:
    now_utc = datetime.now(timezone.utc)
    # Brasília = UTC-3
    from datetime import timedelta

    now_brt = now_utc - timedelta(hours=3)
    return {
        "utc": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "brasilia": now_brt.strftime("%Y-%m-%d %H:%M:%S BRT"),
    }


def _impl_format_brazilian_currency(amount: float) -> dict:
    formatted = f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return {"formatted": formatted, "raw": amount}


_TOOL_IMPLEMENTATIONS = {
    "current_datetime": _impl_current_datetime,
    "format_brazilian_currency": _impl_format_brazilian_currency,
}


# =============================================================================
# Endpoints MCP
# =============================================================================
class CallToolRequest(BaseModel):
    name: str
    arguments: dict


@app.get("/")
def root() -> dict:
    return {
        "service": "Aula 07 MCP Local Mock",
        "protocol": "MCP-like",
        "endpoints": ["/mcp/list_tools", "/mcp/call_tool"],
        "tools_available": list(MCP_TOOLS.keys()),
    }


@app.post("/mcp/list_tools")
def list_tools() -> dict:
    """Retorna lista de tools no formato MCP."""
    return {"tools": list(MCP_TOOLS.values())}


@app.post("/mcp/call_tool")
def call_tool(req: CallToolRequest) -> dict:
    """Executa uma tool e retorna o resultado."""
    if req.name not in _TOOL_IMPLEMENTATIONS:
        raise HTTPException(404, detail=f"Tool '{req.name}' não encontrada")
    try:
        impl = _TOOL_IMPLEMENTATIONS[req.name]
        result = impl(**req.arguments)
        return {"name": req.name, "result": result, "isError": False}
    except Exception as exc:  # noqa: BLE001
        return {"name": req.name, "result": str(exc), "isError": True}
