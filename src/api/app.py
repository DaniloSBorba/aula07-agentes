"""FastAPI app que expõe os agentes via HTTP.

Endpoints:
  GET  /                → info do serviço
  GET  /health          → healthcheck simples
  GET  /product         → config do produto ativo
  POST /agent/single    → roda agente single ReAct
  POST /agent/multi     → roda agente multi LangGraph

Rode com: make serve  (escuta em 0.0.0.0:8000)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.agents.multi_agent import run_multi_agent
from src.agents.single_agent import SingleAgent
from src.config import get_product_config, get_settings


# =============================================================================
# Lifespan
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown da API."""
    settings = get_settings()
    print(f"[API] Produto ativo: {settings.product}")
    print(f"[API] Modelo: {settings.openai_model}")
    yield
    print("[API] Encerrando.")


app = FastAPI(
    title="Aula 07 · Agent API",
    description="Endpoints para os agentes single e multi.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS aberto para uso em sala (Codespaces)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Schemas
# =============================================================================
class AgentRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Pergunta do usuário")
    max_iterations: int = Field(default=2, ge=1, le=4, description="Limite multi-agent")


class StepInfo(BaseModel):
    step_number: int
    tool_name: str | None = None
    tool_args: dict | None = None
    tool_result: str | None = None
    is_final: bool = False
    final_answer: str | None = None


class AgentResponse(BaseModel):
    product: str
    user_query: str
    final_answer: str
    steps: list[StepInfo] = []


class MultiAgentResponse(BaseModel):
    product: str
    user_query: str
    plan: str
    context: str
    draft_answer: str
    critique: str
    final_answer: str
    iterations: int


# =============================================================================
# Endpoints
# =============================================================================
@app.get("/")
def root() -> dict:
    settings = get_settings()
    return {
        "service": "Aula 07 Agent API",
        "version": "1.0.0",
        "active_product": settings.product,
        "model": settings.openai_model,
        "endpoints": [
            "/health", "/product",
            "/agent/single", "/agent/multi",
        ],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/product")
def product() -> dict:
    """Retorna a config do produto ativo (sem persona completa por brevidade)."""
    config = get_product_config()
    return {
        "name": config["name"],
        "description": config["description"],
        "tools": config["tools"],
        "example_prompts": config["example_prompts"],
        "kb_documents": [d["title"] for d in config.get("knowledge_base", [])],
    }


@app.post("/agent/single", response_model=AgentResponse)
def agent_single(req: AgentRequest) -> AgentResponse:
    """Roda o agente single ReAct."""
    try:
        agent = SingleAgent()
        result = agent.run(req.query, verbose=False)
        return AgentResponse(
            product=get_settings().product,
            user_query=result.user_query,
            final_answer=result.final_answer,
            steps=[
                StepInfo(
                    step_number=s.step_number,
                    tool_name=s.tool_name,
                    tool_args=s.tool_args,
                    tool_result=s.tool_result[:1000] if s.tool_result else None,
                    is_final=s.is_final,
                    final_answer=s.final_answer,
                )
                for s in result.steps
            ],
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, detail=str(exc)) from exc


@app.post("/agent/multi", response_model=MultiAgentResponse)
def agent_multi(req: AgentRequest) -> MultiAgentResponse:
    """Roda o agente multi LangGraph (planner → researcher → writer → critic)."""
    try:
        state = run_multi_agent(req.query, max_iterations=req.max_iterations)
        return MultiAgentResponse(
            product=get_settings().product,
            user_query=state.get("user_query", req.query),
            plan=state.get("plan", ""),
            context=state.get("context", "")[:2000],
            draft_answer=state.get("draft_answer", ""),
            critique=state.get("critique", ""),
            final_answer=state.get("final_answer", state.get("draft_answer", "")),
            iterations=state.get("iteration", 0),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, detail=str(exc)) from exc
