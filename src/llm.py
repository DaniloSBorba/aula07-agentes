"""Cliente OpenAI compartilhado.

Um único OpenAI() reusado em toda a aplicação. Cobre tanto LLM quanto juiz.
"""
from functools import lru_cache

from openai import OpenAI

from src.config import get_settings


@lru_cache
def get_openai_client() -> OpenAI:
    """Singleton do cliente OpenAI."""
    settings = get_settings()
    return OpenAI(api_key=settings.openai_api_key)


def chat_completion(
    messages: list[dict],
    model: str | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | dict = "auto",
    temperature: float = 0.7,
    response_format: dict | None = None,
) -> dict:
    """Wrapper sobre chat.completions.create com defaults sensatos.

    Retorna o primeiro `choice.message` como dict (já serializado).
    """
    client = get_openai_client()
    settings = get_settings()

    kwargs: dict = {
        "model": model or settings.openai_model,
        "messages": messages,
        "temperature": temperature,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = tool_choice
    if response_format:
        kwargs["response_format"] = response_format

    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message
    return message.model_dump()
