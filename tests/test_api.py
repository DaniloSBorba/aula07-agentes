"""Tests da API FastAPI (sem chamadas LLM, só schema/health)."""
import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from fastapi.testclient import TestClient

from src.api.app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_has_endpoints():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data
    assert "/agent/single" in data["endpoints"]
    assert "/agent/multi" in data["endpoints"]


def test_product_endpoint():
    response = client.get("/product")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "tools" in data
    assert isinstance(data["tools"], list)


def test_agent_single_validates_input():
    """Query muito curta deve dar 422."""
    response = client.post("/agent/single", json={"query": "oi"})
    assert response.status_code == 422
