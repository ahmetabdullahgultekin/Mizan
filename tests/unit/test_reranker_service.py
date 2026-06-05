"""
Unit tests for the cross-encoder reranker — model-selection single-source-of-truth.

The real CrossEncoder is replaced with a stub so these tests never download a
model. They pin the deliberate model choice documented in
``cross_encoder_service.py``:

* the service constructor default matches ``Settings.reranker_model`` (no drift),
* the factory passes the configured model through verbatim, and
* the *intended* model is the one that is actually loaded.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from mizan.infrastructure.config import Settings
from mizan.infrastructure.reranking.cross_encoder_service import (
    CrossEncoderRerankerService,
)

EXPECTED_DEFAULT = "cross-encoder/ms-marco-MiniLM-L-6-v2"


# ---------------------------------------------------------------------------
# Single source of truth: config default == service constructor default
# ---------------------------------------------------------------------------


def test_config_default_is_english_ms_marco():
    """The configured reranker model is the documented English ms-marco default."""
    assert Settings().reranker_model == EXPECTED_DEFAULT


def test_service_constructor_default_matches_config():
    """Constructing the service with no args must mirror the config default.

    This is the guard that prevents the historical drift where the config
    shipped ms-marco while the service constructor defaulted to jina.
    """
    svc = CrossEncoderRerankerService()
    assert svc.model_name == EXPECTED_DEFAULT
    assert svc.model_name == Settings().reranker_model


def test_default_ms_marco_is_not_multilingual():
    """The English ms-marco default must report as English-only so the search
    service never feeds it Arabic/Turkish text it cannot score."""
    assert CrossEncoderRerankerService().is_multilingual is False


def test_jina_model_is_multilingual():
    """The jina opt-in reports multilingual so the search service routes native
    Arabic/Turkish candidate text to it."""
    jina = "jinaai/jina-reranker-v2-base-multilingual"
    assert CrossEncoderRerankerService(model_name=jina).is_multilingual is True


def test_bge_m3_reranker_is_multilingual():
    """Other multilingual rerankers are recognised by name marker."""
    bge = "BAAI/bge-reranker-v2-m3"
    assert CrossEncoderRerankerService(model_name=bge).is_multilingual is True


# ---------------------------------------------------------------------------
# The intended model is the one that loads
# ---------------------------------------------------------------------------


@pytest.fixture
def stub_sentence_transformers(monkeypatch):
    """Inject a fake ``sentence_transformers`` module exposing CrossEncoder.

    The stub records the model name it was constructed with and reports it back
    via the attributes ``_resolve_loaded_model_name`` probes.
    """
    created: dict[str, object] = {}

    class _FakeConfig:
        def __init__(self, name: str) -> None:
            self._name_or_path = name

    class FakeCrossEncoder:
        def __init__(self, model_name: str, trust_remote_code: bool = False) -> None:
            created["model_name"] = model_name
            created["trust_remote_code"] = trust_remote_code
            self.config = _FakeConfig(model_name)

        def predict(self, pairs):  # pragma: no cover - not exercised here
            return [0.0 for _ in pairs]

    fake_module = types.ModuleType("sentence_transformers")
    fake_module.CrossEncoder = FakeCrossEncoder
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)
    return created


def test_intended_model_is_the_one_loaded(stub_sentence_transformers):
    """``_load_model`` constructs the CrossEncoder with the configured name and
    ``_resolve_loaded_model_name`` confirms the loaded model matches intent."""
    svc = CrossEncoderRerankerService(model_name=EXPECTED_DEFAULT)

    model = svc._load_model()

    assert model is not None
    assert stub_sentence_transformers["model_name"] == EXPECTED_DEFAULT
    # English ms-marco must NOT trigger trust_remote_code (only jina does).
    assert stub_sentence_transformers["trust_remote_code"] is False
    assert svc.is_available is True
    assert svc._resolve_loaded_model_name() == EXPECTED_DEFAULT


def test_jina_opt_in_enables_trust_remote_code(stub_sentence_transformers):
    """The multilingual opt-in sets trust_remote_code, the ms-marco default does not."""
    jina = "jinaai/jina-reranker-v2-base-multilingual"
    svc = CrossEncoderRerankerService(model_name=jina)

    svc._load_model()

    assert stub_sentence_transformers["model_name"] == jina
    assert stub_sentence_transformers["trust_remote_code"] is True


def test_factory_passes_configured_model(monkeypatch, stub_sentence_transformers):
    """get_reranker_service must hand the configured model name to the service."""
    from mizan.infrastructure import reranking

    settings = MagicMock()
    settings.enable_reranking = True
    settings.reranker_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    settings.reranker_top_k = 30
    monkeypatch.setattr(
        "mizan.infrastructure.config.get_settings", lambda: settings
    )
    reranking.get_reranker_service.cache_clear()

    svc = reranking.get_reranker_service()
    try:
        assert svc is not None
        assert svc.model_name == settings.reranker_model
    finally:
        reranking.get_reranker_service.cache_clear()
