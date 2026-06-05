"""
Unit tests for language-aware reranking (feat/search-quality-2026-06-05).

Background
----------
The reranker only ever re-scored candidates that carried an English
``translation_text``, feeding that English text to an English-only cross-encoder.
For Arabic/Turkish queries this meant:
  * raw Arabic verse-vector and keyword hits (no ``translation_text``) were never
    reranked and stayed pinned at the RRF floor, and
  * even when a translation existed, scoring English text against an Arabic query
    is a cross-lingual mismatch the English model cannot handle.

The fix routes candidate text by detected query language AND by reranker
capability (``is_multilingual``):
  * EN query                         -> English translation (then content)
  * non-EN query + EN-only reranker  -> only English translations are scored
                                        (native AR/TR text is NOT fed to a model
                                        that cannot score it; those keep RRF)
  * non-EN query + multilingual      -> native, language-matched text:
                                        AR query -> Arabic ``content``;
                                        TR query -> Turkish translation / content.

These tests pin both the query-language detection and the text-routing matrix
with fully-mocked dependencies (no DB / network / model download).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from mizan.application.services.semantic_search_service import (
    SemanticSearchService,
    detect_query_language,
)
from mizan.domain.entities.library import SemanticSearchResult
from mizan.domain.enums.library_enums import SourceType

# ---------------------------------------------------------------------------
# Query-language detection
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query,expected",
    [
        ("mercy", "en"),
        ("patience and prayer", "en"),
        ("rahmet", "en"),  # no Turkish-specific letter -> generic Latin/EN
        ("sabır", "tr"),
        ("bağışlama", "tr"),
        ("şükür", "tr"),
        ("رحمة", "ar"),
        ("صبر", "ar"),
        ("الصلاة", "ar"),
        ("اللَّهِ", "ar"),  # with harakat
        ("رحمة mercy", "ar"),  # mixed -> Arabic dominates (script present)
    ],
)
def test_detect_query_language(query: str, expected: str) -> None:
    assert detect_query_language(query) == expected


def test_detect_plain_latin_without_turkish_letters_is_en() -> None:
    # "rahmet" has no Turkish-specific letter, so it is treated as generic
    # Latin/English. That is fine: the e5 embedder is multilingual and the
    # reranker routing for "en" (English translation) is a safe default.
    assert detect_query_language("rahmet") == "en"


# ---------------------------------------------------------------------------
# Text routing matrix (_rerank_text_for)
# ---------------------------------------------------------------------------


def _res(
    ref: str,
    content: str = "",
    translation_text: str = "",
    translation_language: str = "",
) -> SemanticSearchResult:
    meta: dict = {}
    if translation_text:
        meta["translation_text"] = translation_text
    if translation_language:
        meta["translation_language"] = translation_language
    return SemanticSearchResult(
        chunk_id=uuid4(),
        text_source_id=uuid4(),
        source_title="Quran",
        source_type=SourceType.QURAN,
        reference=ref,
        content=content,
        similarity_score=0.5,
        metadata=meta,
    )


_pick = SemanticSearchService._rerank_text_for


def test_english_query_prefers_translation() -> None:
    r = _res("1:3", content="ٱلرَّحْمَٰن", translation_text="The Most Merciful", translation_language="en")
    assert _pick(r, "en", multilingual=False) == "The Most Merciful"


def test_english_query_falls_back_to_content() -> None:
    r = _res("1:3", content="ٱلرَّحْمَٰن")
    assert _pick(r, "en", multilingual=False) == "ٱلرَّحْمَٰن"


def test_arabic_query_english_only_reranker_skips_native_text() -> None:
    # English-only reranker must NOT receive Arabic content it cannot score.
    r = _res("1:3", content="ٱلرَّحْمَٰن")
    assert _pick(r, "ar", multilingual=False) == ""


def test_arabic_query_english_only_reranker_uses_english_translation() -> None:
    r = _res("1:3", content="ٱلرَّحْمَٰن", translation_text="The Most Merciful", translation_language="en")
    assert _pick(r, "ar", multilingual=False) == "The Most Merciful"


def test_arabic_query_english_only_skips_turkish_translation() -> None:
    # A TR translation is not scorable by an English-only model under an AR query.
    r = _res("1:3", content="ٱلرَّحْمَٰن", translation_text="Rahmân", translation_language="tr")
    assert _pick(r, "ar", multilingual=False) == ""


def test_arabic_query_multilingual_uses_arabic_content() -> None:
    r = _res("1:3", content="ٱلرَّحْمَٰن", translation_text="The Most Merciful", translation_language="en")
    assert _pick(r, "ar", multilingual=True) == "ٱلرَّحْمَٰن"


def test_turkish_query_multilingual_prefers_turkish_translation() -> None:
    r = _res("1:3", content="ٱلرَّحْمَٰن", translation_text="Rahmân", translation_language="tr")
    assert _pick(r, "tr", multilingual=True) == "Rahmân"


def test_turkish_query_multilingual_falls_back_to_content() -> None:
    # No TR translation on this candidate -> a same-script anchor (Arabic) beats
    # nothing; content is returned.
    r = _res("1:3", content="ٱلرَّحْمَٰن", translation_text="The Most Merciful", translation_language="en")
    assert _pick(r, "tr", multilingual=True) == "ٱلرَّحْمَٰن"


# ---------------------------------------------------------------------------
# End-to-end: Arabic query + multilingual reranker reranks native verse hits
# ---------------------------------------------------------------------------


def _make_service_with_reranker(reranker, **kwargs) -> SemanticSearchService:
    embedder = MagicMock()
    embedder.embed_text = AsyncMock(return_value=[0.1] * 768)

    verse_repo = MagicMock()
    verse_repo.search_by_text = AsyncMock(return_value=kwargs.get("verse_results", []))
    verse_repo.keyword_search_verses = AsyncMock(
        return_value=kwargs.get("keyword_verse_results", [])
    )
    chunk_repo = MagicMock()
    chunk_repo.semantic_search = AsyncMock(return_value=[])
    chunk_repo.keyword_search_chunks = AsyncMock(return_value=[])
    translation_repo = MagicMock()
    translation_repo.search_by_text = AsyncMock(
        return_value=kwargs.get("translation_results", [])
    )

    return SemanticSearchService(
        chunk_repo=chunk_repo,
        verse_emb_repo=verse_repo,
        embedding_service=embedder,
        reranker=reranker,
        reranker_top_k=30,
        verse_translation_repo=translation_repo,
    )


@pytest.mark.asyncio
async def test_arabic_query_multilingual_reranker_reranks_native_hits() -> None:
    """
    With a MULTILINGUAL reranker, an Arabic query must feed Arabic verse text to
    the reranker for candidates that have NO English translation (the historical
    blind spot). The mock reranker promotes whichever doc contains 'صبر' so we
    can assert the native hit was actually scored and reordered.
    """
    # Two Arabic verse-vector hits with NO translation_text (the blind spot).
    # The "strong" verse carries an unambiguous marker token the fake reranker
    # keys on, so the assertion does not hinge on harakat-exact substring matching.
    strong_marker = "بالصبر"  # un-vocalised "with patience"
    verse_hits = [
        _res("2:61", content="لن نصبر على طعام"),           # weak match
        _res("2:153", content=f"استعينوا {strong_marker} والصلاة"),  # strong
    ]
    # Give 2:61 a higher upstream score so that, withOUT reranking, 2:61 ranks first.
    verse_hits[0].similarity_score = 0.9
    verse_hits[1].similarity_score = 0.6

    captured: dict = {}

    async def fake_rerank(query, documents, top_k=None):
        captured["documents"] = list(documents)
        # Score: the doc containing the strong marker token wins.
        scored = [
            (i, 1.0 if strong_marker in d else 0.1) for i, d in enumerate(documents)
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    reranker = MagicMock()
    reranker.rerank = AsyncMock(side_effect=fake_rerank)
    reranker.is_multilingual = True
    reranker.model_name = "jinaai/jina-reranker-v2-base-multilingual"

    svc = _make_service_with_reranker(reranker, verse_results=verse_hits)

    results = await svc.search(query="صبر", source_types=[SourceType.QURAN], limit=10)

    # The reranker received the NATIVE Arabic verse text (not empty, not English).
    assert "documents" in captured
    assert any(strong_marker in d for d in captured["documents"])
    # And the strong native hit (2:153) is now ranked first despite its lower
    # upstream cosine — proving native reranking took effect.
    assert results[0].reference == "2:153"


@pytest.mark.asyncio
async def test_reranked_scores_map_to_correct_candidate() -> None:
    """Regression: ``rerank()`` returns (doc_index, score) sorted by score; the
    service must map each score back to the candidate via the RETURNED doc index,
    not the enumerate position. The old code used the enumerate position, which
    assigned reranked scores to the wrong verses once the list was score-sorted.

    Three candidates A,B,C; the reranker ranks them C(0.9) > A(0.5) > B(0.1).
    The final order must be C, A, B with those exact scores attached.
    """
    cand = [
        _res("A", content="alpha", translation_text="alpha", translation_language="en"),
        _res("B", content="bravo", translation_text="bravo", translation_language="en"),
        _res("C", content="charlie", translation_text="charlie", translation_language="en"),
    ]
    # Distinct upstream scores so RRF order is A,B,C before reranking.
    cand[0].similarity_score, cand[1].similarity_score, cand[2].similarity_score = 0.9, 0.8, 0.7

    async def fake_rerank(query, documents, top_k=None):
        # documents == ["alpha", "bravo", "charlie"]; rank C>A>B, return sorted.
        score_by_text = {"charlie": 0.9, "alpha": 0.5, "bravo": 0.1}
        scored = [(i, score_by_text[d]) for i, d in enumerate(documents)]
        scored.sort(key=lambda x: x[1], reverse=True)  # -> [(2,.9),(0,.5),(1,.1)]
        return scored

    reranker = MagicMock()
    reranker.rerank = AsyncMock(side_effect=fake_rerank)
    reranker.is_multilingual = False
    reranker.model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    svc = _make_service_with_reranker(reranker, verse_results=cand)
    results = await svc.search(query="x", source_types=[SourceType.QURAN], limit=10)

    assert [r.reference for r in results] == ["C", "A", "B"]
    assert results[0].similarity_score == pytest.approx(0.9)
    assert results[1].similarity_score == pytest.approx(0.5)
    assert results[2].similarity_score == pytest.approx(0.1)


@pytest.mark.asyncio
async def test_arabic_query_english_only_reranker_does_not_rerank_native_hits() -> None:
    """
    With an ENGLISH-ONLY reranker, an Arabic query must NOT feed Arabic text to
    the model. Candidates with no English translation keep their RRF order.
    """
    verse_hits = [
        _res("2:61", content="لَن نَّصْبِرَ"),
        _res("2:153", content="بِٱلصَّبْرِ"),
    ]

    captured: dict = {"called_with": None}

    async def fake_rerank(query, documents, top_k=None):
        captured["called_with"] = list(documents)
        return [(i, 0.5) for i in range(len(documents))]

    reranker = MagicMock()
    reranker.rerank = AsyncMock(side_effect=fake_rerank)
    reranker.is_multilingual = False
    reranker.model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    svc = _make_service_with_reranker(reranker, verse_results=verse_hits)

    await svc.search(query="صبر", source_types=[SourceType.QURAN], limit=10)

    # Either rerank was never called (no scorable docs) or it was called with an
    # empty document list — never with Arabic content.
    docs = captured["called_with"]
    assert docs is None or docs == [] or all("ص" not in d for d in docs)
