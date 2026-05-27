"""Tests do servidor MCP local mock."""
import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient

from src.mcp.server import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "tools_available" in data
    assert "current_datetime" in data["tools_available"]


def test_list_tools():
    response = client.post("/mcp/list_tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) >= 2


def test_call_tool_datetime():
    response = client.post(
        "/mcp/call_tool",
        json={"name": "current_datetime", "arguments": {}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["isError"] is False
    assert "utc" in data["result"]
    assert "brasilia" in data["result"]


def test_call_tool_currency():
    response = client.post(
        "/mcp/call_tool",
        json={"name": "format_brazilian_currency", "arguments": {"amount": 1234.5}},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["isError"] is False
    assert "R$" in data["result"]["formatted"]
    assert "1.234,50" in data["result"]["formatted"]


def test_call_tool_nonexistent():
    response = client.post(
        "/mcp/call_tool",
        json={"name": "tool_que_nao_existe", "arguments": {}},
    )
    assert response.status_code == 404
