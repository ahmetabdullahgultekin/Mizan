"""
Unit tests for the model-aware embedding prefix policy.

The prefix convention (e5's ``query: ``/``passage: `` vs none for other models)
is what makes ``EMBEDDING_MODEL`` swappable without silently degrading recall.
These tests pin:

* the policy resolved for each known model family,
* that the e5 default (prod) is unchanged,
* that the ``SentenceTransformerEmbeddingService`` exposes the right prefixes
  *without loading the model* (so no download happens in CI), and
* that the search/indexing modules' documented constants stay in sync with the
  single source of truth (``E5_POLICY``).

No model is ever downloaded: the prefix policy is derived from the model *name*.
"""

from __future__ import annotations

import dataclasses

import pytest

from mizan.infrastructure.embeddings.prefix_policy import (
    E5_POLICY,
    NO_PREFIX_POLICY,
    EmbeddingPrefixPolicy,
    prefix_policy_for,
)
from mizan.infrastructure.embeddings.sentence_transformer_service import (
    SentenceTransformerEmbeddingService,
)

# ---------------------------------------------------------------------------
# prefix_policy_for — model-name → policy resolution
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "model_name",
    [
        "intfloat/multilingual-e5-base",
        "intfloat/multilingual-e5-large",
        "intfloat/multilingual-e5-small",
        "intfloat/e5-large-v2",
        "e5-large",
        "INTFLOAT/MULTILINGUAL-E5-LARGE",  # case-insensitive
    ],
)
def test_e5_family_gets_query_passage_prefixes(model_name: str) -> None:
    policy = prefix_policy_for(model_name)
    assert policy == E5_POLICY
    assert policy.query_prefix == "query: "
    assert policy.passage_prefix == "passage: "


@pytest.mark.parametrize(
    "model_name",
    [
        "BAAI/bge-m3",
        "BAAI/bge-reranker-v2-m3",
        "Alibaba-NLP/gte-multilingual-base",
        "text-embedding-004",
        "gemini-embedding-2-preview",
        "sentence-transformers/all-MiniLM-L6-v2",
        "",
        "some/unknown-model",
    ],
)
def test_non_e5_models_get_no_prefix(model_name: str) -> None:
    policy = prefix_policy_for(model_name)
    assert policy == NO_PREFIX_POLICY
    assert policy.query_prefix == ""
    assert policy.passage_prefix == ""


def test_policy_applies_prefixes() -> None:
    assert E5_POLICY.for_query("mercy") == "query: mercy"
    assert E5_POLICY.for_passage("الرحمن") == "passage: الرحمن"
    assert NO_PREFIX_POLICY.for_query("mercy") == "mercy"
    assert NO_PREFIX_POLICY.for_passage("الرحمن") == "الرحمن"


def test_policy_is_frozen() -> None:
    """The policy is immutable so it can be safely shared as a constant."""
    with pytest.raises(dataclasses.FrozenInstanceError):
        EmbeddingPrefixPolicy().query_prefix = "x"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Backend selection — SentenceTransformerEmbeddingService exposes the policy
# WITHOUT loading the model (no download in tests).
# ---------------------------------------------------------------------------


def test_e5_base_backend_reports_e5_prefixes_without_loading() -> None:
    svc = SentenceTransformerEmbeddingService("intfloat/multilingual-e5-base")
    assert svc.query_prefix() == "query: "
    assert svc.passage_prefix() == "passage: "
    # The model itself must NOT have been loaded just to read the prefix.
    assert svc._model is None


def test_e5_large_backend_is_selectable_and_keeps_e5_prefixes() -> None:
    """Switching EMBEDDING_MODEL to e5-large keeps the correct e5 prefixes."""
    svc = SentenceTransformerEmbeddingService("intfloat/multilingual-e5-large")
    assert svc.model_name == "intfloat/multilingual-e5-large"
    assert svc.query_prefix() == "query: "
    assert svc.passage_prefix() == "passage: "
    assert svc._model is None


def test_non_e5_backend_reports_no_prefix() -> None:
    svc = SentenceTransformerEmbeddingService("BAAI/bge-m3")
    assert svc.query_prefix() == ""
    assert svc.passage_prefix() == ""
    assert svc._model is None


def test_default_backend_is_e5_base() -> None:
    """The zero-arg backend mirrors the prod default (unchanged behaviour)."""
    svc = SentenceTransformerEmbeddingService()
    assert svc.model_name == "intfloat/multilingual-e5-base"
    assert svc.query_prefix() == "query: "
    assert svc.passage_prefix() == "passage: "


# ---------------------------------------------------------------------------
# Single source of truth — app-layer constants mirror E5_POLICY
# ---------------------------------------------------------------------------


def test_search_query_prefix_constant_matches_policy() -> None:
    from mizan.application.services.semantic_search_service import QUERY_PREFIX

    assert QUERY_PREFIX == E5_POLICY.query_prefix


def test_indexing_passage_prefix_constant_matches_policy() -> None:
    from mizan.application.services.indexing_service import PASSAGE_PREFIX

    assert PASSAGE_PREFIX == E5_POLICY.passage_prefix


# ---------------------------------------------------------------------------
# Wiring — the search service embeds the query with the BACKEND's prefix,
# so a no-prefix backend does NOT get an injected 'query: '.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_uses_backend_query_prefix() -> None:
    from unittest.mock import AsyncMock, MagicMock

    from mizan.application.services.semantic_search_service import SemanticSearchService

    embedder = MagicMock()
    embedder.embed_text = AsyncMock(return_value=[0.1] * 768)
    embedder.query_prefix = MagicMock(return_value="query: ")  # e5 backend

    verse_repo = MagicMock()
    verse_repo.search_by_text = AsyncMock(return_value=[])
    verse_repo.keyword_search_verses = AsyncMock(return_value=[])
    chunk_repo = MagicMock()
    chunk_repo.semantic_search = AsyncMock(return_value=[])
    chunk_repo.keyword_search_chunks = AsyncMock(return_value=[])

    svc = SemanticSearchService(
        chunk_repo=chunk_repo,
        verse_emb_repo=verse_repo,
        embedding_service=embedder,
    )
    await svc.search("mercy", limit=5)

    # The e5 backend's 'query: ' prefix must be prepended before embedding.
    embedder.embed_text.assert_awaited_once_with("query: mercy")


@pytest.mark.asyncio
async def test_search_with_prefixless_backend_injects_nothing() -> None:
    from unittest.mock import AsyncMock, MagicMock

    from mizan.application.services.semantic_search_service import SemanticSearchService

    embedder = MagicMock()
    embedder.embed_text = AsyncMock(return_value=[0.1] * 768)
    embedder.query_prefix = MagicMock(return_value="")  # e.g. gemini / bge-m3

    verse_repo = MagicMock()
    verse_repo.search_by_text = AsyncMock(return_value=[])
    verse_repo.keyword_search_verses = AsyncMock(return_value=[])
    chunk_repo = MagicMock()
    chunk_repo.semantic_search = AsyncMock(return_value=[])
    chunk_repo.keyword_search_chunks = AsyncMock(return_value=[])

    svc = SemanticSearchService(
        chunk_repo=chunk_repo,
        verse_emb_repo=verse_repo,
        embedding_service=embedder,
    )
    await svc.search("mercy", limit=5)

    # A prefix-less backend must NOT have 'query: ' injected.
    embedder.embed_text.assert_awaited_once_with("mercy")


def test_iembedding_default_prefixes_are_empty() -> None:
    """The port's default prefix accessors return '' so non-e5 impls are safe."""
    from mizan.domain.services.embedding_service import IEmbeddingService

    class _Dummy(IEmbeddingService):
        async def embed_text(self, text: str) -> list[float]:
            return [0.0]

        async def embed_batch(self, texts: list[str]) -> list[list[float]]:
            return [[0.0] for _ in texts]

        @property
        def model_name(self) -> str:
            return "dummy"

        @property
        def embedding_dimension(self) -> int:
            return 1

    d = _Dummy()
    assert d.query_prefix() == ""
    assert d.passage_prefix() == ""
