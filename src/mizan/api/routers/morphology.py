"""Morphology endpoints for word-level Quranic Arabic analysis."""

from typing import Any

from fastapi import APIRouter, Path, Query

from mizan.api.dependencies import MorphologyRepo

router = APIRouter()

# Morphology is structurally live, but the linguistic fields (root / lemma /
# pattern) are only populated once the Quranic Arabic Corpus (QAC/MASAQ) dataset
# is ingested into `data/masaq/` (see scripts/ingest_masaq.py). Until then those
# fields come back null. We surface a `data_status` flag on every response so
# clients never mistake an empty `root` for a verified "this word has no root".
_PREVIEW_NOTE = (
    "Linguistic fields (root/lemma/pattern) require the Quranic Arabic Corpus "
    "dataset, which is not yet loaded. Segmentation/POS may be present but "
    "roots/lemmas will be null. This is preview output, not verified morphology."
)


def _data_status(has_linguistic_data: bool) -> dict[str, Any]:
    """Build the data-availability envelope shared by all morphology responses."""
    if has_linguistic_data:
        return {"data_status": "complete", "preview": False}
    return {"data_status": "preview", "preview": True, "note": _PREVIEW_NOTE}


@router.get("/morphology/verse/{surah}/{verse}")
async def get_verse_morphology(
    morphology_repo: MorphologyRepo,
    surah: int = Path(..., ge=1, le=114, description="Surah number"),
    verse: int = Path(..., ge=1, description="Verse number"),
) -> dict[str, Any]:
    """
    Get morphological analysis for all words in a verse.

    Returns a list of words, each containing its morpheme segments
    with POS tags, roots, lemmas, and grammatical features.
    """
    from mizan.domain.value_objects import VerseLocation

    location = VerseLocation(surah, verse)
    words = await morphology_repo.get_verse_morphology(location)

    has_roots = any(
        seg.root or seg.lemma for segments in words for seg in segments
    )

    return {
        "surah": surah,
        "verse": verse,
        "word_count": len(words),
        **_data_status(has_roots),
        "words": [
            {
                "word_number": word_idx + 1,
                "segments": [
                    {
                        "morpheme_type": seg.morpheme_type,
                        "pos_tag": seg.pos_tag,
                        "word_uthmani": seg.word_uthmani,
                        "word_imlaei": seg.word_imlaei,
                        "root": seg.root,
                        "lemma": seg.lemma,
                        "pattern": seg.pattern,
                        "person": seg.person,
                        "gender": seg.gender,
                        "number": seg.number,
                        "case_state": seg.case_state,
                        "mood_voice": seg.mood_voice,
                        "syntactic_role": seg.syntactic_role,
                        "irab_description": seg.irab_description,
                    }
                    for seg in segments
                ],
            }
            for word_idx, segments in enumerate(words)
        ],
    }


@router.get("/morphology/word/{surah}/{verse}/{word}")
async def get_word_morphology(
    morphology_repo: MorphologyRepo,
    surah: int = Path(..., ge=1, le=114, description="Surah number"),
    verse: int = Path(..., ge=1, description="Verse number"),
    word: int = Path(..., ge=1, description="Word position in verse (1-indexed)"),
) -> dict[str, Any]:
    """
    Get morphological analysis for a specific word.

    Returns all morpheme segments (prefix, stem, suffix) for the
    word at the given position within the verse.
    """
    from mizan.domain.value_objects import VerseLocation

    location = VerseLocation(surah, verse)
    segments = await morphology_repo.get_word_morphology(location, word)

    if not segments:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail=f"No morphology data found for word {word} at {surah}:{verse}",
        )

    has_roots = any(seg.root or seg.lemma for seg in segments)

    return {
        "surah": surah,
        "verse": verse,
        "word_number": word,
        "segment_count": len(segments),
        **_data_status(has_roots),
        "segments": [
            {
                "morpheme_type": seg.morpheme_type,
                "pos_tag": seg.pos_tag,
                "word_uthmani": seg.word_uthmani,
                "word_imlaei": seg.word_imlaei,
                "root": seg.root,
                "lemma": seg.lemma,
                "pattern": seg.pattern,
                "person": seg.person,
                "gender": seg.gender,
                "number": seg.number,
                "case_state": seg.case_state,
                "mood_voice": seg.mood_voice,
                "syntactic_role": seg.syntactic_role,
                "irab_description": seg.irab_description,
            }
            for seg in segments
        ],
    }


@router.get("/morphology/search/root/{root}")
async def search_by_root(
    morphology_repo: MorphologyRepo,
    root: str = Path(..., min_length=1, max_length=20, description="Arabic root (e.g., كتب)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
) -> dict[str, Any]:
    """
    Search for all occurrences of an Arabic root in the Quran.

    The root should be provided without dashes or separators
    (e.g., 'كتب' not 'ك-ت-ب').
    """
    results = await morphology_repo.search_by_root(root)

    # Apply limit
    limited = results[:limit]

    return {
        "root": root,
        "total_occurrences": len(results),
        "returned": len(limited),
        **_data_status(bool(results)),
        "occurrences": [
            {
                "surah": loc.surah_number,
                "verse": loc.verse_number,
                "word_number": word_num,
            }
            for loc, word_num in limited
        ],
    }


@router.get("/morphology/roots/frequency")
async def get_root_frequency(
    morphology_repo: MorphologyRepo,
    limit: int = Query(50, ge=1, le=500, description="Number of top roots to return"),
) -> dict[str, Any]:
    """
    Get the most frequent Arabic roots in the Quran.

    Returns roots sorted by occurrence count in descending order.
    """
    freq = await morphology_repo.get_root_frequency()

    # Sort by frequency (already sorted from repo, but ensure)
    sorted_roots = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    top_roots = sorted_roots[:limit]

    return {
        "total_unique_roots": len(freq),
        "returned": len(top_roots),
        **_data_status(bool(freq)),
        "roots": [
            {
                "root": root,
                "count": count,
            }
            for root, count in top_roots
        ],
    }
