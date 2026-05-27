"""Configurações centralizadas da aplicação.

Carrega de variáveis de ambiente (.env) e do arquivo config/products.yaml.
Validado por pydantic — falha cedo se algo crítico estiver faltando.
"""
from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"


class Settings(BaseSettings):
    """Variáveis de ambiente da aplicação."""

    # OpenAI
    openai_api_key: str = Field(..., description="Chave da OpenAI (sk-...)")
    openai_model: str = Field(default="gpt-4.1-mini")
    openai_judge_model: str = Field(default="gpt-4.1")

    # Produto ativo
    product: Literal["educiacao", "designmind"] = Field(default="educiacao")

    # API
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    # MCP
    mcp_host: str = Field(default="127.0.0.1")
    mcp_port: int = Field(default=8001)

    # Logging
    log_level: str = Field(default="INFO")

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Singleton de Settings. Carrega uma vez e reusa."""
    return Settings()  # type: ignore[call-arg]


@lru_cache
def get_product_config() -> dict:
    """Carrega config do produto ativo a partir do config/products.yaml."""
    settings = get_settings()
    products_file = CONFIG_DIR / "products.yaml"
    with products_file.open(encoding="utf-8") as f:
        all_products = yaml.safe_load(f)

    if settings.product not in all_products:
        raise ValueError(
            f"Produto '{settings.product}' não encontrado no products.yaml. "
            f"Opções: {list(all_products.keys())}"
        )

    return all_products[settings.product]
