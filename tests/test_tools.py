"""Tests offline das tools. NÃO precisam de OPENAI_API_KEY."""
import os

import pytest

# Garantir que tests rodam sem chave válida
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-for-offline-tests")


def test_calculator_basic():
    from src.tools.calculator import run_calculator

    assert "= 7" in run_calculator("3 + 4")
    assert "= 1.875" in run_calculator("3/4 * 5/2") or "= 15/8" in run_calculator("3/4 * 5/2")
    assert "ERRO" in run_calculator("import os")  # bloqueia código


def test_calculator_unsafe_blocked():
    from src.tools.calculator import run_calculator

    assert "ERRO" in run_calculator("__import__('os').system('ls')")


def test_grade_classifier_fundamental():
    from src.tools.grade_classifier import run_grade_level_classifier

    result = run_grade_level_classifier("Estou no sexto ano e tenho dificuldade com fração")
    assert "Fundamental" in result


def test_grade_classifier_medio():
    from src.tools.grade_classifier import run_grade_level_classifier

    result = run_grade_level_classifier("Preciso aprender Bhaskara para o vestibular")
    assert "Médio" in result


def test_design_phase_validator_empatizar():
    from src.tools.design_validator import run_design_phase_validator

    result = run_design_phase_validator("Quero entender meu cliente, fazer entrevista")
    assert "EMPATIZAR" in result


def test_design_phase_validator_idear():
    from src.tools.design_validator import run_design_phase_validator

    result = run_design_phase_validator("Preciso de brainstorm para gerar ideias")
    assert "IDEAR" in result


def test_ideation_prompt_generator():
    from src.tools.ideation_generator import run_ideation_prompt_generator

    result = run_ideation_prompt_generator("aumentar retenção", count=5)
    assert "How Might We" in result or "Como podemos" in result
    # Deve gerar 5 prompts numerados
    assert "1." in result and "5." in result


@pytest.mark.parametrize("product", ["educiacao", "designmind"])
def test_product_config_loads(product, monkeypatch):
    """Carrega config dos dois produtos."""
    monkeypatch.setenv("PRODUCT", product)
    # Limpar cache lru_cache
    from src.config import get_product_config, get_settings

    get_settings.cache_clear()
    get_product_config.cache_clear()

    config = get_product_config()
    assert "persona" in config
    assert "tools" in config
    assert len(config["example_prompts"]) >= 3
