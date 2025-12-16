"""
Analyzer service - Orchestrates analysis operations.

This is the main application service that coordinates
domain services, repositories, and caching.
"""

from typing import Any

from mizan.domain.enums import AbjadSystem, NormalizationLevel, ScriptType
from mizan.domain.repositories import IQuranRepository
from mizan.domain.services import AbjadCalculator, LetterCounter, WordCounter
from mizan.domain.value_objects import VerseLocation
from mizan.infrastructure.cache.redis_cache import RedisCache
from mizan.infrastructure.text.normalizer import ArabicNormalizer


class AnalyzerService:
    """
    Application service for text analysis operations.

    Coordinates domain services, repositories, and caching
    to fulfill analysis use cases.
    """

    def __init__(
        self,
        quran_repository: IQuranRepository,
        cache: RedisCache | None = None,
    ) -> None:
        """
        Initialize analyzer service.

        Args:
            quran_repository: Repository for verse access
            cache: Optional Redis cache
        """
        self._repo = quran_repository
        self._cache = cache

        # Domain services
        self._letter_counter = LetterCounter()
        self._word_counter = WordCounter()
        self._abjad_calculator = AbjadCalculator()
        self._normalizer = ArabicNormalizer()

    async def count_letters(
        self,
        surah_number: int | None = None,
        verse_number: int | None = None,
        script_type: ScriptType = ScriptType.UTHMANI,
        count_alif_wasla: bool = True,
        count_alif_khanjariyya: bool = True,
    ) -> dict[str, Any]:
        """
        Count letters in specified scope.

        Args:
            surah_number: Filter by surah (None = all)
            verse_number: Filter by verse (requires surah)
            script_type: Script to analyze
            count_alif_wasla: Include Alif Wasla
            count_alif_khanjariyya: Include Alif Khanjariyya

        Returns:
            Dictionary with count and methodology
        """
        # Check cache
        cache_key = f"letters:{surah_number}:{verse_number}:{script_type.value}"
        if self._cache:
            cached = await self._cache.get("analysis", cache_key)
            if cached:
                return cached

        # Get text
        text = await self._get_text(surah_number, verse_number, script_type)

        # Count
        count = self._letter_counter.count_letters(
            text,
            count_alif_wasla=count_alif_wasla,
            count_alif_khanjariyya=count_alif_khanjariyya,
        )

        result = {
            "count": count,
            "scope": {
                "surah": surah_number,
                "verse": verse_number,
                "script": script_type.value,
            },
            "methodology": (
                f"Arabic letter count with Alif Wasla={'counted' if count_alif_wasla else 'excluded'}, "
                f"Alif Khanjariyya={'counted' if count_alif_khanjariyya else 'excluded'}"
            ),
        }

        # Cache result
        if self._cache:
            await self._cache.set("analysis", cache_key, result)

        return result

    async def count_words(
        self,
        surah_number: int | None = None,
        verse_number: int | None = None,
        script_type: ScriptType = ScriptType.UTHMANI,
    ) -> dict[str, Any]:
        """
        Count words in specified scope.

        Returns dictionary with count, methodology, and audit trail.
        """
        cache_key = f"words:{surah_number}:{verse_number}:{script_type.value}"
        if self._cache:
            cached = await self._cache.get("analysis", cache_key)
            if cached:
                return cached

        text = await self._get_text(surah_number, verse_number, script_type)
        word_result = self._word_counter.count_words(text)

        result = {
            "count": word_result.count,
            "scope": {
                "surah": surah_number,
                "verse": verse_number,
                "script": script_type.value,
            },
            "methodology": word_result.methodology,
            "audit": word_result.to_audit_dict(),
        }

        if self._cache:
            await self._cache.set("analysis", cache_key, result)

        return result

    async def calculate_abjad(
        self,
        text: str | None = None,
        surah_number: int | None = None,
        verse_number: int | None = None,
        system: AbjadSystem = AbjadSystem.MASHRIQI,
        include_breakdown: bool = False,
    ) -> dict[str, Any]:
        """
        Calculate Abjad value.

        Args:
            text: Direct text to calculate (optional)
            surah_number: Surah to calculate
            verse_number: Verse to calculate
            system: Abjad system (Mashriqi or Maghribi)
            include_breakdown: Include letter-by-letter breakdown

        Returns:
            Dictionary with value, system, and optionally breakdown
        """
        if text is None:
            text = await self._get_text(surah_number, verse_number)

        abjad_value = self._abjad_calculator.calculate(text, system)

        result = {
            "value": abjad_value.value,
            "system": system.value,
            "text_length": len(text),
            "is_prime": abjad_value.is_prime(),
            "digital_root": abjad_value.digital_root(),
        }

        if include_breakdown:
            result["breakdown"] = [
                {"letter": letter, "value": value}
                for letter, value in abjad_value.letter_breakdown
            ]

        return result

    async def get_letter_frequency(
        self,
        surah_number: int | None = None,
        verse_number: int | None = None,
        script_type: ScriptType = ScriptType.UTHMANI,
        normalize_variants: bool = True,
    ) -> dict[str, Any]:
        """
        Get letter frequency distribution.

        Returns dictionary mapping letters to their counts.
        """
        text = await self._get_text(surah_number, verse_number, script_type)
        frequency = self._letter_counter.get_letter_frequency(text, normalize_variants)

        # Sort by frequency (descending)
        sorted_freq = sorted(frequency.items(), key=lambda x: x[1], reverse=True)

        return {
            "frequency": dict(sorted_freq),
            "total_letters": sum(frequency.values()),
            "unique_letters": len(frequency),
            "top_10": sorted_freq[:10],
            "scope": {
                "surah": surah_number,
                "verse": verse_number,
            },
        }

    async def get_verse(
        self,
        surah_number: int,
        verse_number: int,
    ) -> dict[str, Any]:
        """
        Get a single verse with all metadata.
        """
        location = VerseLocation(surah_number, verse_number)
        verse = await self._repo.get_verse_or_raise(location)

        return {
            "surah_number": verse.surah_number,
            "verse_number": verse.verse_number,
            "text_uthmani": verse.text_uthmani,
            "text_simple": verse.content.get(ScriptType.SIMPLE),
            "juz_number": verse.juz_number,
            "hizb_number": verse.hizb_number,
            "manzil_number": verse.manzil_number,
            "page_number": verse.page_number,
            "ruku_number": verse.ruku_number,
            "is_sajdah": verse.is_sajdah,
            "sajdah_type": verse.sajdah_type.value if verse.sajdah_type else None,
            "word_count": verse.word_count,
            "letter_count": verse.letter_count,
            "abjad_value": verse.abjad_value_mashriqi,
            "surah_name_arabic": verse.surah_metadata.name_arabic,
            "surah_name_english": verse.surah_metadata.name_english,
        }

    async def search_text(
        self,
        query: str,
        surah_number: int | None = None,
        normalization: NormalizationLevel = NormalizationLevel.FULL,
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Search for text in the Quran.

        Args:
            query: Search query
            surah_number: Optional surah filter
            normalization: Normalization level for matching
            limit: Maximum results

        Returns:
            Search results with matches
        """
        # Normalize query
        normalized_query = self._normalizer.normalize(query, normalization)

        # Search using repository
        verses = await self._repo.search_text(
            normalized_query,
            surah_number=surah_number,
            case_sensitive=False,
        )

        results = []
        for verse in verses[:limit]:
            results.append({
                "surah_number": verse.surah_number,
                "verse_number": verse.verse_number,
                "text": verse.text_uthmani,
                "surah_name": verse.surah_metadata.name_arabic,
            })

        return {
            "query": query,
            "normalized_query": normalized_query,
            "total_results": len(verses),
            "results": results,
            "methodology": f"Text search with {normalization.value} normalization",
        }

    async def _get_text(
        self,
        surah_number: int | None,
        verse_number: int | None,
        script_type: ScriptType = ScriptType.UTHMANI,
    ) -> str:
        """Get text for the specified scope."""
        if verse_number is not None:
            if surah_number is None:
                raise ValueError("verse_number requires surah_number")
            location = VerseLocation(surah_number, verse_number)
            verse = await self._repo.get_verse_or_raise(location)
            return verse.get_text(script_type)

        if surah_number is not None:
            surah = await self._repo.get_surah(surah_number)
            return surah.get_full_text(script_type)

        # All verses
        verses = await self._repo.get_all_verses()
        return "\n".join(v.get_text(script_type) for v in verses)
