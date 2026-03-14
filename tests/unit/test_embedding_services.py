"""
Unit tests for embedding services.

Tests CascadeEmbeddingService fallback logic and dimension mismatch detection.
All external dependencies (primary/fallback providers) are replaced with AsyncMocks.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from mizan.infrastructure.embeddings.cascade_service import CascadeEmbeddingService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_service(model_name: str, dimension: int) -> MagicMock:
    """Return a mock IEmbeddingService with controlled properties."""
    svc = MagicMock()
    svc.model_name = model_name
    svc.embedding_dimension = dimension
    svc.embed_batch = AsyncMock(return_value=[[0.1] * dimension])
    svc.embed_text = AsyncMock(return_value=[0.1] * dimension)
    return svc


# ---------------------------------------------------------------------------
# CascadeEmbeddingService — construction
# ---------------------------------------------------------------------------


def test_cascade_raises_on_dimension_mismatch():
    """CascadeEmbeddingService.__init__ raises ValueError when dimensions differ."""
    primary = _make_mock_service("primary-model", 768)
    fallback = _make_mock_service("fallback-model", 512)

    with pytest.raises(ValueError, match="matching embedding dimensions"):
        CascadeEmbeddingService(primary=primary, fallback=fallback)


def test_cascade_accepts_matching_dimensions():
    """CascadeEmbeddingService initialises successfully when dimensions match."""
    primary = _make_mock_service("primary-model", 768)
    fallback = _make_mock_service("fallback-model", 768)
    svc = CascadeEmbeddingService(primary=primary, fallback=fallback)
    assert svc.embedding_dimension == 768


# ---------------------------------------------------------------------------
# CascadeEmbeddingService — model_name property
# ---------------------------------------------------------------------------


def test_cascade_model_name_returns_primary_when_not_using_fallback():
    primary = _make_mock_service("gemini-primary", 768)
    fallback = _make_mock_service("local-fallback", 768)
    svc = CascadeEmbeddingService(primary=primary, fallback=fallback)
    assert svc.model_name == "gemini-primary"


@pytest.mark.asyncio
async def test_cascade_model_name_returns_fallback_after_primary_fails():
    primary = _make_mock_service("gemini-primary", 768)
    primary.embed_batch = AsyncMock(side_effect=RuntimeError("API down"))
    fallback = _make_mock_service("local-fallback", 768)

    svc = CascadeEmbeddingService(primary=primary, fallback=fallback)
    await svc.embed_batch(["test"])
    assert "[fallback]" in svc.model_name
    assert "local-fallback" in svc.model_name


# ---------------------------------------------------------------------------
# CascadeEmbeddingService — fallback behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cascade_uses_primary_when_it_succeeds():
    primary = _make_mock_service("primary", 768)
    fallback = _make_mock_service("fallback", 768)

    svc = CascadeEmbeddingService(primary=primary, fallback=fallback)
    result = await svc.embed_batch(["hello"])

    primary.embed_batch.assert_called_once_with(["hello"])
    fallback.embed_batch.assert_not_called()
    assert result == [[0.1] * 768]
    assert svc.is_using_fallback is False


@pytest.mark.asyncio
async def test_cascade_switches_to_fallback_when_primary_raises():
    primary = _make_mock_service("primary", 768)
    primary.embed_batch = AsyncMock(side_effect=Exception("connection error"))
    fallback = _make_mock_service("fallback", 768)

    svc = CascadeEmbeddingService(primary=primary, fallback=fallback)
    result = await svc.embed_batch(["hello"])

    fallback.embed_batch.assert_called_once_with(["hello"])
    assert result == [[0.1] * 768]
    assert svc.is_using_fallback is True


@pytest.mark.asyncio
async def test_cascade_recovers_to_primary_after_it_succeeds_again():
    primary = _make_mock_service("primary", 768)
    # Fail first call, succeed second
    primary.embed_batch = AsyncMock(
        side_effect=[Exception("transient error"), [[0.2] * 768]]
    )
    fallback = _make_mock_service("fallback", 768)

    svc = CascadeEmbeddingService(primary=primary, fallback=fallback)

    # First call triggers fallback
    await svc.embed_batch(["first"])
    assert svc.is_using_fallback is True

    # Second call primary recovers
    result = await svc.embed_batch(["second"])
    assert result == [[0.2] * 768]
    assert svc.is_using_fallback is False


@pytest.mark.asyncio
async def test_cascade_embed_text_delegates_to_embed_batch():
    primary = _make_mock_service("primary", 768)
    fallback = _make_mock_service("fallback", 768)

    svc = CascadeEmbeddingService(primary=primary, fallback=fallback)
    result = await svc.embed_text("single text")

    primary.embed_batch.assert_called_once_with(["single text"])
    assert result == [0.1] * 768


# ---------------------------------------------------------------------------
# CascadeEmbeddingService — status helpers
# ---------------------------------------------------------------------------


def test_cascade_primary_model_property():
    primary = _make_mock_service("gemini-768", 768)
    fallback = _make_mock_service("e5-base", 768)
    svc = CascadeEmbeddingService(primary=primary, fallback=fallback)
    assert svc.primary_model == "gemini-768"


def test_cascade_fallback_model_property():
    primary = _make_mock_service("gemini-768", 768)
    fallback = _make_mock_service("e5-base", 768)
    svc = CascadeEmbeddingService(primary=primary, fallback=fallback)
    assert svc.fallback_model == "e5-base"


def test_cascade_dimension_legacy_alias():
    """The `.dimension` property is a legacy alias for `.embedding_dimension`."""
    primary = _make_mock_service("primary", 768)
    fallback = _make_mock_service("fallback", 768)
    svc = CascadeEmbeddingService(primary=primary, fallback=fallback)
    assert svc.dimension == svc.embedding_dimension


# ---------------------------------------------------------------------------
# Factory — dimension mismatch at startup
# ---------------------------------------------------------------------------


def test_factory_raises_on_dimension_mismatch(monkeypatch):
    """get_embedding_service raises ValueError when primary/fallback dims differ."""
    from mizan.infrastructure.embeddings import factory

    primary_svc = _make_mock_service("primary", 768)
    fallback_svc = _make_mock_service("fallback", 512)

    settings = MagicMock()
    settings.embedding_provider = "local"
    settings.embedding_model = "primary-model"
    settings.embedding_fallback_provider = "gemini"
    settings.embedding_fallback_model = "fallback-model"
    settings.gemini_api_key = "key"

    monkeypatch.setattr(factory, "get_settings", lambda: settings)
    monkeypatch.setattr(factory, "_create_single_service", lambda provider, model, s: (
        primary_svc if model == "primary-model" else fallback_svc
    ))

    # Clear the lru_cache so our monkeypatched get_settings is used
    factory.get_embedding_service.cache_clear()

    with pytest.raises(ValueError, match="dimension"):
        factory.get_embedding_service()

    # Clean up for other tests
    factory.get_embedding_service.cache_clear()
