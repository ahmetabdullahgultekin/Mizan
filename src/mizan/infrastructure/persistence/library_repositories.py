"""
SQLAlchemy implementations of library repository interfaces.

These adapters translate between domain entities and database models,
and implement vector similarity search using pgvector's cosine distance.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

import structlog
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from mizan.domain.entities.library import (
    LibrarySpace,
    SemanticSearchResult,
    TextChunk,
    TextSource,
    VerseEmbedding,
    VerseTranslation,
)
from mizan.domain.enums.library_enums import IndexingStatus, SourceType
from mizan.domain.repositories.library_interfaces import (
    ILibrarySpaceRepository,
    ITextChunkRepository,
    ITextSourceRepository,
    IVerseEmbeddingRepository,
    IVerseTranslationRepository,
)
from mizan.infrastructure.persistence.models import (
    LibrarySpaceModel,
    TextChunkModel,
    TextSourceModel,
    VerseEmbeddingModel,
    VerseTranslationModel,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------


def _space_to_domain(m: LibrarySpaceModel) -> LibrarySpace:
    return LibrarySpace(
        id=m.id,
        name=m.name,
        description=m.description,
        created_at=m.created_at,
    )


def _source_to_domain(m: TextSourceModel) -> TextSource:
    return TextSource(
        id=m.id,
        library_space_id=m.library_space_id,
        source_type=SourceType(m.source_type),
        title_arabic=m.title_arabic,
        title_turkish=m.title_turkish,
        title_english=m.title_english,
        author=m.author,
        status=IndexingStatus(m.status),
        total_chunks=m.total_chunks,
        indexed_chunks=m.indexed_chunks,
        embedding_model=m.embedding_model,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _chunk_to_domain(m: TextChunkModel) -> TextChunk:
    return TextChunk(
        id=m.id,
        text_source_id=m.text_source_id,
        chunk_index=m.chunk_index,
        content=m.content,
        reference=m.reference,
        embedding=list(m.embedding) if m.embedding is not None else None,
        metadata=m.metadata_ or {},
        created_at=m.created_at,
    )


def _verse_emb_to_domain(m: VerseEmbeddingModel) -> VerseEmbedding:
    return VerseEmbedding(
        id=m.id,
        verse_id=m.verse_id,
        surah_number=m.surah_number,
        verse_number=m.verse_number,
        embedding=list(m.embedding),
        model_name=m.model_name,
        created_at=m.created_at,
    )


# ---------------------------------------------------------------------------
# LibrarySpace Repository
# ---------------------------------------------------------------------------


class PostgresLibrarySpaceRepository(ILibrarySpaceRepository):
    """PostgreSQL-backed library space repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, space: LibrarySpace) -> LibrarySpace:
        model = LibrarySpaceModel(
            id=space.id,
            name=space.name,
            description=space.description,
            created_at=space.created_at,
        )
        self._session.add(model)
        await self._session.flush()
        logger.info("library_space_created", space_id=str(space.id), name=space.name)
        return space

    async def get_by_id(self, space_id: UUID) -> LibrarySpace | None:
        result = await self._session.execute(
            select(LibrarySpaceModel).where(LibrarySpaceModel.id == space_id)
        )
        model = result.scalar_one_or_none()
        return _space_to_domain(model) if model else None

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LibrarySpace]:
        stmt = (
            select(LibrarySpaceModel)
            .order_by(LibrarySpaceModel.created_at)
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_space_to_domain(m) for m in result.scalars().all()]

    async def delete(self, space_id: UUID) -> bool:
        result = await self._session.execute(
            delete(LibrarySpaceModel).where(LibrarySpaceModel.id == space_id)
        )
        found = bool(result.rowcount and result.rowcount > 0)  # type: ignore[attr-defined]
        logger.info("library_space_deleted", space_id=str(space_id), found=found)
        return found


# ---------------------------------------------------------------------------
# TextSource Repository
# ---------------------------------------------------------------------------


class PostgresTextSourceRepository(ITextSourceRepository):
    """PostgreSQL-backed text source repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, source: TextSource) -> TextSource:
        logger.info(
            "text_source_creating", source_id=str(source.id), source_type=source.source_type.value
        )
        model = TextSourceModel(
            id=source.id,
            library_space_id=source.library_space_id,
            source_type=source.source_type.value,
            title_arabic=source.title_arabic,
            title_turkish=source.title_turkish,
            title_english=source.title_english,
            author=source.author,
            status=source.status.value,
            total_chunks=source.total_chunks,
            indexed_chunks=source.indexed_chunks,
            embedding_model=source.embedding_model,
            created_at=source.created_at,
            updated_at=source.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        logger.info("text_source_created", source_id=str(source.id))
        return source

    async def get_by_id(self, source_id: UUID) -> TextSource | None:
        result = await self._session.execute(
            select(TextSourceModel).where(TextSourceModel.id == source_id)
        )
        model = result.scalar_one_or_none()
        return _source_to_domain(model) if model else None

    async def get_by_space(
        self,
        space_id: UUID,
        source_type: SourceType | None = None,
    ) -> list[TextSource]:
        stmt = select(TextSourceModel).where(TextSourceModel.library_space_id == space_id)
        if source_type is not None:
            stmt = stmt.where(TextSourceModel.source_type == source_type.value)
        stmt = stmt.order_by(TextSourceModel.created_at)
        result = await self._session.execute(stmt)
        return [_source_to_domain(m) for m in result.scalars().all()]

    async def update_status(
        self,
        source_id: UUID,
        status: IndexingStatus,
        indexed_chunks: int | None = None,
        total_chunks: int | None = None,
        embedding_model: str | None = None,
    ) -> TextSource | None:
        values: dict[str, object] = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
        }
        if indexed_chunks is not None:
            values["indexed_chunks"] = indexed_chunks
        if total_chunks is not None:
            values["total_chunks"] = total_chunks
        if embedding_model is not None:
            values["embedding_model"] = embedding_model

        await self._session.execute(
            update(TextSourceModel).where(TextSourceModel.id == source_id).values(**values)
        )
        await self._session.flush()
        return await self.get_by_id(source_id)

    async def delete(self, source_id: UUID) -> bool:
        result = await self._session.execute(
            delete(TextSourceModel).where(TextSourceModel.id == source_id)
        )
        return bool(result.rowcount and result.rowcount > 0)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# TextChunk Repository
# ---------------------------------------------------------------------------


class PostgresTextChunkRepository(ITextChunkRepository):
    """PostgreSQL + pgvector text chunk repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_batch(self, chunks: list[TextChunk]) -> list[TextChunk]:
        models = [
            TextChunkModel(
                id=chunk.id,
                text_source_id=chunk.text_source_id,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                reference=chunk.reference,
                embedding=None,
                metadata_=chunk.metadata,
                created_at=chunk.created_at,
            )
            for chunk in chunks
        ]
        self._session.add_all(models)
        await self._session.flush()
        return chunks

    async def update_embedding(
        self,
        chunk_id: UUID,
        embedding: list[float],
    ) -> None:
        await self._session.execute(
            update(TextChunkModel).where(TextChunkModel.id == chunk_id).values(embedding=embedding)
        )

    async def update_embeddings_batch(
        self,
        updates: list[tuple[UUID, list[float]]],
    ) -> None:
        for chunk_id, embedding in updates:
            await self._session.execute(
                update(TextChunkModel)
                .where(TextChunkModel.id == chunk_id)
                .values(embedding=embedding)
            )
        await self._session.flush()

    async def get_by_source(self, source_id: UUID) -> list[TextChunk]:
        result = await self._session.execute(
            select(TextChunkModel)
            .where(TextChunkModel.text_source_id == source_id)
            .order_by(TextChunkModel.chunk_index)
        )
        return [_chunk_to_domain(m) for m in result.scalars().all()]

    async def semantic_search(
        self,
        query_embedding: list[float],
        library_space_id: UUID | None = None,
        source_types: list[SourceType] | None = None,
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> list[SemanticSearchResult]:
        """
        Cosine similarity search using pgvector's <=> operator.

        The <=> operator computes cosine distance (0=identical, 2=opposite).
        We convert to similarity: similarity = 1 - distance.
        """
        from sqlalchemy import text as sa_text

        # Build the base query with cosine distance
        # 1 - (embedding <=> query) gives cosine similarity
        # Convert numpy floats to plain Python floats for pgvector
        clean_embedding = [float(x) for x in query_embedding]
        params: dict[str, object] = {"embedding": str(clean_embedding), "limit": limit}

        where_clauses = ["tc.embedding IS NOT NULL"]

        if library_space_id is not None:
            where_clauses.append("ts.library_space_id = :library_space_id")
            params["library_space_id"] = str(library_space_id)

        if source_types:
            type_values = [st.value for st in source_types]
            placeholders = ", ".join(f":stype_{i}" for i in range(len(type_values)))
            where_clauses.append(f"ts.source_type IN ({placeholders})")
            for i, val in enumerate(type_values):
                params[f"stype_{i}"] = val

        if min_similarity > 0:
            # cosine distance = 1 - similarity, so distance < 1 - min_sim
            max_distance = 1.0 - min_similarity
            where_clauses.append(f"(tc.embedding <=> CAST(:embedding AS vector)) < {max_distance}")

        where_sql = " AND ".join(where_clauses)

        sql = sa_text(f"""
            SELECT
                tc.id         AS chunk_id,
                tc.text_source_id,
                COALESCE(ts.title_arabic, '') AS source_title,
                ts.source_type,
                tc.reference,
                tc.content,
                (1 - (tc.embedding <=> CAST(:embedding AS vector))) AS similarity_score,
                tc.metadata
            FROM text_chunks tc
            JOIN text_sources ts ON tc.text_source_id = ts.id
            WHERE {where_sql}
            ORDER BY tc.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)  # nosec B608

        result = await self._session.execute(sql, params)
        rows = result.fetchall()

        return [
            SemanticSearchResult(
                chunk_id=row.chunk_id,
                text_source_id=row.text_source_id,
                source_title=row.source_title,
                source_type=SourceType(row.source_type),
                reference=row.reference,
                content=row.content,
                similarity_score=float(row.similarity_score),
                metadata=row.metadata or {},
            )
            for row in rows
        ]

    async def keyword_search_chunks(
        self,
        query: str,
        source_types: list[SourceType] | None = None,
        limit: int = 20,
    ) -> list[SemanticSearchResult]:
        """
        Full-text keyword search on text_chunks.content using tsvector + GIN.

        Uses plainto_tsquery('simple', query) for tsvector matching and
        a LIKE fallback with Arabic orthography variant generation.
        """
        from sqlalchemy import text as sa_text

        # Reuse the verse repo's variant generation for Arabic search
        search_variants = PostgresVerseEmbeddingRepository._arabic_search_variants(query)

        params: dict[str, object] = {"query": query, "limit": limit}

        # Build ILIKE conditions for each variant
        ilike_conditions = []
        for i, variant in enumerate(search_variants):
            param_name = f"variant_{i}"
            params[param_name] = variant
            ilike_conditions.append(
                f"tc.content ILIKE '%' || :{param_name} || '%'"
            )

        ilike_sql = " OR ".join(ilike_conditions) if ilike_conditions else "FALSE"

        where_clauses = [
            f"(tc.content_search_vector @@ plainto_tsquery('simple', :query)"
            f" OR {ilike_sql})"
        ]

        if source_types:
            type_values = [st.value for st in source_types]
            placeholders = ", ".join(f":stype_{i}" for i in range(len(type_values)))
            where_clauses.append(f"ts.source_type IN ({placeholders})")
            for i, val in enumerate(type_values):
                params[f"stype_{i}"] = val

        where_sql = " AND ".join(where_clauses)

        sql = sa_text(f"""
            SELECT
                tc.id         AS chunk_id,
                tc.text_source_id,
                COALESCE(ts.title_arabic, '') AS source_title,
                ts.source_type,
                tc.reference,
                tc.content,
                GREATEST(
                    ts_rank(tc.content_search_vector, plainto_tsquery('simple', :query)),
                    CASE WHEN {ilike_sql} THEN 0.1 ELSE 0.0 END
                ) AS rank_score,
                tc.metadata
            FROM text_chunks tc
            JOIN text_sources ts ON tc.text_source_id = ts.id
            WHERE {where_sql}
            ORDER BY rank_score DESC
            LIMIT :limit
        """)  # nosec B608

        result = await self._session.execute(sql, params)
        rows = result.fetchall()

        # Normalize rank scores to 0-1 range
        max_rank = max((float(row.rank_score) for row in rows), default=1.0) or 1.0

        return [
            SemanticSearchResult(
                chunk_id=row.chunk_id,
                text_source_id=row.text_source_id,
                source_title=row.source_title,
                source_type=SourceType(row.source_type),
                reference=row.reference,
                content=row.content,
                similarity_score=round(float(row.rank_score) / max_rank, 4),
                metadata=row.metadata or {},
            )
            for row in rows
        ]

    async def delete_by_source(self, source_id: UUID) -> int:
        result = await self._session.execute(
            delete(TextChunkModel).where(TextChunkModel.text_source_id == source_id)
        )
        return int(result.rowcount or 0)  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# VerseEmbedding Repository
# ---------------------------------------------------------------------------


class PostgresVerseEmbeddingRepository(IVerseEmbeddingRepository):
    """PostgreSQL + pgvector verse embedding repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, verse_embedding: VerseEmbedding) -> VerseEmbedding:
        """Insert or replace a verse embedding for a (verse_id, model_name) pair."""
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(VerseEmbeddingModel).values(
            id=verse_embedding.id,
            verse_id=verse_embedding.verse_id,
            surah_number=verse_embedding.surah_number,
            verse_number=verse_embedding.verse_number,
            embedding=verse_embedding.embedding,
            model_name=verse_embedding.model_name,
            created_at=verse_embedding.created_at,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_verse_embedding_model",
            set_={
                "embedding": stmt.excluded.embedding,
                "created_at": stmt.excluded.created_at,
            },
        )
        await self._session.execute(stmt)
        await self._session.flush()
        return verse_embedding

    async def upsert_batch(self, embeddings: list[VerseEmbedding]) -> int:
        for ve in embeddings:
            await self.upsert(ve)
        await self._session.flush()
        logger.debug("verse_embeddings_upserted", count=len(embeddings))
        return len(embeddings)

    async def get_by_verse(
        self,
        surah_number: int,
        verse_number: int,
        model_name: str | None = None,
    ) -> VerseEmbedding | None:
        stmt = select(VerseEmbeddingModel).where(
            VerseEmbeddingModel.surah_number == surah_number,
            VerseEmbeddingModel.verse_number == verse_number,
        )
        if model_name:
            stmt = stmt.where(VerseEmbeddingModel.model_name == model_name)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _verse_emb_to_domain(model) if model else None

    async def find_similar_verses(
        self,
        query_embedding: list[float],
        limit: int = 10,
        exclude_surah: int | None = None,
        exclude_verse: int | None = None,
    ) -> list[tuple[int, int, float]]:
        """Find most similar verses using pgvector cosine distance."""
        from sqlalchemy import text as sa_text

        where_clauses = []
        # Convert numpy floats to plain Python floats for pgvector
        clean_embedding = [float(x) for x in query_embedding]
        params: dict[str, object] = {"embedding": str(clean_embedding), "limit": limit}

        if exclude_surah is not None and exclude_verse is not None:
            where_clauses.append("NOT (surah_number = :excl_surah AND verse_number = :excl_verse)")
            params["excl_surah"] = exclude_surah
            params["excl_verse"] = exclude_verse

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        sql = sa_text(f"""
            SELECT
                surah_number,
                verse_number,
                (1 - (embedding <=> CAST(:embedding AS vector))) AS similarity_score
            FROM verse_embeddings
            {where_sql}
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)  # nosec B608

        result = await self._session.execute(sql, params)
        rows = result.fetchall()

        return [
            (int(row.surah_number), int(row.verse_number), float(row.similarity_score))
            for row in rows
        ]

    async def search_by_text(
        self,
        query_embedding: list[float],
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> list[SemanticSearchResult]:
        """
        Search verse embeddings by a free-text query embedding.

        JOINs with the verses table to return actual verse content as
        SemanticSearchResult objects for unified search results.
        """
        from sqlalchemy import text as sa_text

        clean_embedding = [float(x) for x in query_embedding]
        params: dict[str, object] = {"embedding": str(clean_embedding), "limit": limit}

        where_clauses = ["ve.embedding IS NOT NULL"]

        if min_similarity > 0:
            max_distance = 1.0 - min_similarity
            where_clauses.append(f"(ve.embedding <=> CAST(:embedding AS vector)) < {max_distance}")

        where_sql = " AND ".join(where_clauses)

        sql = sa_text(f"""
            SELECT
                ve.id            AS chunk_id,
                ve.verse_id      AS text_source_id,
                'القرآن الكريم'  AS source_title,
                'QURAN'          AS source_type,
                (ve.surah_number || ':' || ve.verse_number) AS reference,
                v.text_uthmani   AS content,
                (1 - (ve.embedding <=> CAST(:embedding AS vector))) AS similarity_score
            FROM verse_embeddings ve
            JOIN verses v ON v.surah_number = ve.surah_number
                         AND v.verse_number = ve.verse_number
            WHERE {where_sql}
            ORDER BY ve.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)  # nosec B608

        result = await self._session.execute(sql, params)
        rows = result.fetchall()

        return [
            SemanticSearchResult(
                chunk_id=row.chunk_id,
                text_source_id=row.text_source_id,
                source_title=row.source_title,
                source_type=SourceType(row.source_type),
                reference=row.reference,
                content=row.content,
                similarity_score=float(row.similarity_score),
                metadata={
                    "surah_number": int(row.reference.split(":")[0]),
                    "verse_number": int(row.reference.split(":")[1]),
                },
            )
            for row in rows
        ]

    # Common Arabic stop words that should not be used as ILIKE search terms
    # (they appear in nearly every verse and would drown out specific matches)
    _ARABIC_STOP_WORDS = frozenset({
        "من", "في", "على", "إلى", "عن", "مع", "هو", "هي", "هم", "هن",
        "ما", "لا", "ان", "أن", "إن", "كل", "بل", "قد", "لم", "لن",
        "ثم", "أو", "بن", "ذا", "تلك", "هذا", "هذه", "ذلك", "التي",
        "الذي", "الذين", "التى", "كان", "كانت", "يكن", "ليس", "بعد",
        "قبل", "حتى", "عند", "بين", "فوق", "تحت", "كما", "لما",
        "وما", "ولا", "فلا", "إلا", "ألا",
        # Turkish stop words (common in mixed queries)
        "ve", "ile", "bir", "bu", "de", "da",
        # English stop words
        "the", "and", "to", "of", "in", "for", "is", "on", "at", "by",
        "with", "from", "that", "this", "not", "are", "was", "were",
        "patience", "mother", "father",  # too generic in English
    })

    # -----------------------------------------------------------------------
    # ISRI-based Arabic Stemmer (pure Python, no NLTK dependency)
    #
    # Based on the ISRI stemmer algorithm by Kazem Taghva, Rania Elkhoury,
    # and Jeffrey Coombs. Uses an exhaustive multi-strategy approach:
    # try all combinations of prefix/suffix/augmentation stripping and
    # infixed-alef removal, then select the best 3-letter root candidate.
    #
    # Handles Arabic morphology including:
    # - Definite article (ال) and conjunction prefixes (و، ف، ب، ك، ل)
    # - Compound prefixes (بال، وال، فال، كال، لل)
    # - Pronoun suffixes (ه، ها، هم، هن، ك، كم، كن، نا)
    # - Plural/dual suffixes (ون، ين، ات، ان، تين، تان)
    # - Ta marbuta (ة) and alef maqsura (ى)
    # - Verbal/augmentation prefixes (أ، م، ن، ت، ي)
    # - Infixed alef in فاعل and فعال patterns
    # -----------------------------------------------------------------------

    # Compound prefixes (article + preposition combinations)
    _ISRI_P1 = ("بال", "وال", "فال", "كال", "لل", "ال")
    # Single-char prefixes (conjunctions, prepositions)
    _ISRI_P2 = ("و", "ف", "ب", "ك", "ل")
    # Suffixes ordered by length: 3-char, 2-char, 1-char
    _ISRI_S3 = ("تين", "تان")
    _ISRI_S2 = ("ون", "ين", "ات", "ان", "ها", "هم", "هن", "كم", "كن", "نا", "يه", "يك")
    _ISRI_S1 = ("ة", "ه", "ي", "ك", "ت", "ا", "ن")
    _ISRI_ALL_SUFFIXES = _ISRI_S3 + _ISRI_S2 + _ISRI_S1
    # Augmentation prefixes (verbal forms, participles)
    _ISRI_AUG = ("ا", "م", "ن", "ت", "ي")

    @classmethod
    def _try_reduce_to_root(cls, s: str) -> list[str]:
        """
        Recursively try all ways to reduce a stem to a 3-letter root.

        Attempts augmentation prefix removal, suffix removal, and
        infixed-alef removal (فاعل→فعل, فعال→فعل patterns).
        """
        if len(s) < 3:
            return []
        if len(s) == 3:
            return [s]
        results: list[str] = []
        # Infixed alef at position 1 (فاعل → فعل, e.g. والد→ولد, صابر→صبر)
        if len(s) == 4 and s[1] == "\u0627":
            results.append(s[0] + s[2:])
        # Infixed alef at position 2 (فعال → فعل, e.g. حسان→حسن, جمال→جمل)
        if len(s) == 4 and s[2] == "\u0627":
            results.append(s[:2] + s[3:])
        # Augmentation prefix removal (ا، م، ن، ت، ي)
        for a in cls._ISRI_AUG:
            if s.startswith(a) and len(s) - 1 >= 3:
                results.extend(cls._try_reduce_to_root(s[1:]))
        # Suffix removal
        for sf in cls._ISRI_ALL_SUFFIXES:
            if s.endswith(sf) and len(s) - len(sf) >= 3:
                results.extend(cls._try_reduce_to_root(s[:-len(sf)]))
        return results

    @classmethod
    def _extract_arabic_root(cls, word: str) -> str | None:
        """
        ISRI-based Arabic stemmer: extract the 3-letter root.

        Uses an exhaustive approach — tries all combinations of prefix
        stripping, suffix stripping, augmentation removal, and infixed-alef
        removal. Collects all possible 3-letter root candidates, then
        selects the best one (preferring roots without alef, since true
        Arabic consonantal roots rarely contain alef).

        Handles all morphological forms:
          الوالدين، والديه، بولديه، ولديك → ولد
          الصبر، صابرين، اصبر، فاصبر → صبر
          احسانا، إحسان، المحسنين → حسن
        """
        if not word or len(word) < 3:
            return None

        stem = word

        # Normalize alef variants → plain alef
        for ch in "\u0671\u0623\u0625\u0622":  # ٱأإآ
            stem = stem.replace(ch, "\u0627")  # ا
        # Alef maqsura → ya (common in roots)
        if stem.endswith("\u0649"):  # ى
            stem = stem[:-1] + "\u064A"  # ي

        if len(stem) == 3:
            return stem

        # Build all possible prefix-stripped forms
        prefix_stripped: list[str] = [stem]  # always try with no prefix removed

        for pf in cls._ISRI_P1:
            if stem.startswith(pf) and len(stem) - len(pf) >= 2:
                prefix_stripped.append(stem[len(pf):])
        for pf in cls._ISRI_P2:
            if stem.startswith(pf) and len(stem) - len(pf) >= 2:
                after_pf = stem[len(pf):]
                prefix_stripped.append(after_pf)
                # Also try single prefix + ال (e.g., و+ال+والدين)
                if after_pf.startswith("\u0627\u0644") and len(after_pf) - 2 >= 2:
                    prefix_stripped.append(after_pf[2:])

        # For each prefix-stripped form, try recursive reduction + suffix paths
        candidates: list[str] = []
        for ps in prefix_stripped:
            # Full recursive reduction (all suffix/aug/infixed-alef combos)
            candidates.extend(cls._try_reduce_to_root(ps))
            # Also try stripping one suffix first (allowing shorter remainders)
            for sf in cls._ISRI_ALL_SUFFIXES:
                if ps.endswith(sf) and len(ps) - len(sf) >= 2:
                    candidates.extend(cls._try_reduce_to_root(ps[:-len(sf)]))

        # Select best candidate: prefer 3-char roots, and among those
        # prefer roots without alef (true Arabic roots rarely contain alef)
        three_char = [c for c in candidates if len(c) == 3]
        if three_char:
            no_alef = [c for c in three_char if "\u0627" not in c]
            if no_alef:
                return no_alef[0]
            return three_char[0]

        valid = [c for c in candidates if len(c) >= 3]
        if valid:
            return min(valid, key=len)

        return stem if len(stem) >= 3 else None

    @staticmethod
    def _arabic_search_variants(query: str) -> list[str]:
        """
        Generate per-word search variants for Arabic Quranic orthography.

        For each word in the query, generates:
        1. Original word (for exact matches)
        2. Alef-normalized version (ٱأإآ → ا)
        3. Alef-stripped version (Uthmani often drops alef)
        4. ISRI-stemmed root (the 3-letter core that catches all forms)

        The ISRI root is the most important variant — it catches all
        morphological forms: والدين, بولديه, ولديك, الوالدات → ولد.
        """
        alef_chars = "ٱأإآ"
        plain_alef = "ا"
        stop_words = PostgresVerseEmbeddingRepository._ARABIC_STOP_WORDS
        extract_root = PostgresVerseEmbeddingRepository._extract_arabic_root

        variants: set[str] = set()

        for word in query.split():
            # Skip stop words and very short words
            if word in stop_words or len(word) < 3:
                continue

            # 1. Original word
            variants.add(word)

            # 2. Alef-normalized version
            normalized = word
            for ch in alef_chars:
                normalized = normalized.replace(ch, plain_alef)
            if normalized != word:
                variants.add(normalized)

            # 3. Alef-stripped version (Uthmani script often omits alef)
            stripped = normalized.replace(plain_alef, "")
            if len(stripped) >= 3:
                variants.add(stripped)

            # 4. ISRI-stemmed root from the original word
            #    This is the KEY improvement: proper Arabic stemming
            root = extract_root(word)
            if root and root not in stop_words:
                variants.add(root)
                # Also add root with alef stripped (for Uthmani matching)
                root_no_alef = root.replace(plain_alef, "")
                if len(root_no_alef) >= 3:
                    variants.add(root_no_alef)

            # Also try root from the alef-normalized form
            root_norm = extract_root(normalized)
            if root_norm and root_norm != root and root_norm not in stop_words:
                variants.add(root_norm)
                root_norm_no_alef = root_norm.replace(plain_alef, "")
                if len(root_norm_no_alef) >= 3:
                    variants.add(root_norm_no_alef)

        return [v for v in variants if len(v) >= 3 and v not in stop_words]

    async def keyword_search_verses(
        self,
        query: str,
        limit: int = 20,
    ) -> list[SemanticSearchResult]:
        """
        Full-text keyword search on verses.text_no_tashkeel using tsvector + GIN.

        Uses plainto_tsquery('simple', query) for tsvector matching and
        a LIKE fallback for direct substring matching. Generates multiple
        search variants to handle Quranic orthography differences (e.g.,
        والدين → ولدين, where Uthmani script drops alef).
        Returns results as SemanticSearchResult for unified search merging.
        """
        from sqlalchemy import text as sa_text

        # Generate search variants for Arabic orthography differences
        search_variants = self._arabic_search_variants(query)

        params: dict[str, object] = {"query": query, "limit": limit}

        # Build ILIKE conditions for each variant
        ilike_conditions = []
        for i, variant in enumerate(search_variants):
            param_name = f"variant_{i}"
            params[param_name] = variant
            ilike_conditions.append(
                f"v.text_no_tashkeel ILIKE '%' || :{param_name} || '%'"
            )

        ilike_sql = " OR ".join(ilike_conditions) if ilike_conditions else "FALSE"

        # Build per-variant CASE expressions that count how many variants match.
        # Verses matching more query words rank higher (e.g., ولد + صبر > ولد alone).
        match_count_parts = []
        for i in range(len(search_variants)):
            param_name = f"variant_{i}"
            match_count_parts.append(
                f"CASE WHEN v.text_no_tashkeel ILIKE '%' || :{param_name} || '%' THEN 1 ELSE 0 END"
            )
        match_count_sql = " + ".join(match_count_parts) if match_count_parts else "0"

        sql = sa_text(f"""
            SELECT
                v.id             AS chunk_id,
                v.id             AS text_source_id,
                'القرآن الكريم'  AS source_title,
                'QURAN'          AS source_type,
                (v.surah_number || ':' || v.verse_number) AS reference,
                v.text_uthmani   AS content,
                GREATEST(
                    ts_rank(v.text_search_vector, plainto_tsquery('simple', :query)),
                    ({match_count_sql}) * 0.1
                ) AS rank_score
            FROM verses v
            WHERE v.text_search_vector @@ plainto_tsquery('simple', :query)
               OR {ilike_sql}
            ORDER BY rank_score DESC
            LIMIT :limit
        """)  # nosec B608

        result = await self._session.execute(sql, params)
        rows = result.fetchall()

        # Normalize rank scores to 0-1 range
        max_rank = max((float(row.rank_score) for row in rows), default=1.0) or 1.0

        return [
            SemanticSearchResult(
                chunk_id=row.chunk_id,
                text_source_id=row.text_source_id,
                source_title=row.source_title,
                source_type=SourceType(row.source_type),
                reference=row.reference,
                content=row.content,
                similarity_score=round(float(row.rank_score) / max_rank, 4),
                metadata={
                    "surah_number": int(row.reference.split(":")[0]),
                    "verse_number": int(row.reference.split(":")[1]),
                },
            )
            for row in rows
        ]

    async def get_total_count(self, model_name: str | None = None) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(VerseEmbeddingModel)
        if model_name:
            stmt = stmt.where(VerseEmbeddingModel.model_name == model_name)
        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def get_embedded_verse_keys(self, model_name: str | None = None) -> set[tuple[int, int]]:
        """Return a set of (surah_number, verse_number) for already-embedded verses.

        Used by embed_quran.py to skip verses that already have embeddings,
        enabling checkpoint/resume on interrupted embedding runs.
        """
        stmt = select(VerseEmbeddingModel.surah_number, VerseEmbeddingModel.verse_number)
        if model_name:
            stmt = stmt.where(VerseEmbeddingModel.model_name == model_name)
        result = await self._session.execute(stmt)
        return {(int(row.surah_number), int(row.verse_number)) for row in result.fetchall()}


# ---------------------------------------------------------------------------
# Mapping helper – VerseTranslation
# ---------------------------------------------------------------------------


def _verse_trans_to_domain(m: VerseTranslationModel) -> VerseTranslation:
    return VerseTranslation(
        id=m.id,
        verse_id=m.verse_id,
        surah_number=m.surah_number,
        verse_number=m.verse_number,
        language=m.language,
        translation_text=m.translation_text,
        source_name=m.source_name,
        resource_id=m.resource_id,
        embedding=list(m.embedding) if m.embedding is not None else None,
        model_name=m.model_name,
        created_at=m.created_at,
    )


# ---------------------------------------------------------------------------
# VerseTranslation Repository
# ---------------------------------------------------------------------------


class PostgresVerseTranslationRepository(IVerseTranslationRepository):
    """PostgreSQL + pgvector verse translation repository for cross-lingual search."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_batch(self, translations: list[VerseTranslation]) -> int:
        """Insert or update a batch of verse translations. Returns count."""
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        for t in translations:
            stmt = pg_insert(VerseTranslationModel).values(
                id=t.id,
                verse_id=t.verse_id,
                surah_number=t.surah_number,
                verse_number=t.verse_number,
                language=t.language,
                translation_text=t.translation_text,
                source_name=t.source_name,
                resource_id=t.resource_id,
                embedding=t.embedding,
                model_name=t.model_name,
                created_at=t.created_at,
            )
            stmt = stmt.on_conflict_do_update(
                constraint="uq_verse_translation",
                set_={
                    "translation_text": stmt.excluded.translation_text,
                    "source_name": stmt.excluded.source_name,
                    "created_at": stmt.excluded.created_at,
                },
            )
            await self._session.execute(stmt)

        await self._session.flush()
        logger.debug("verse_translations_upserted", count=len(translations))
        return len(translations)

    async def search_by_text(
        self,
        query_embedding: list[float],
        language: str | None = None,
        limit: int = 10,
        min_similarity: float = 0.0,
    ) -> list[SemanticSearchResult]:
        """
        Search translation embeddings and return Arabic text_uthmani as content.

        Matches against translation embeddings (same-language matching) but
        returns the original Arabic verse text so the user sees Quranic text.
        """
        from sqlalchemy import text as sa_text

        clean_embedding = [float(x) for x in query_embedding]
        params: dict[str, object] = {"embedding": str(clean_embedding), "limit": limit}

        where_clauses = ["vt.embedding IS NOT NULL"]

        if language is not None:
            where_clauses.append("vt.language = :language")
            params["language"] = language

        if min_similarity > 0:
            max_distance = 1.0 - min_similarity
            where_clauses.append(
                f"(vt.embedding <=> CAST(:embedding AS vector)) < {max_distance}"
            )

        where_sql = " AND ".join(where_clauses)

        sql = sa_text(f"""
            SELECT
                vt.id            AS chunk_id,
                vt.verse_id      AS text_source_id,
                vt.source_name   AS source_title,
                'QURAN'          AS source_type,
                (vt.surah_number || ':' || vt.verse_number) AS reference,
                v.text_uthmani   AS content,
                (1 - (vt.embedding <=> CAST(:embedding AS vector))) AS similarity_score,
                vt.language      AS trans_language,
                vt.translation_text AS translation_text
            FROM verse_translations vt
            JOIN verses v ON v.surah_number = vt.surah_number
                         AND v.verse_number = vt.verse_number
            WHERE {where_sql}
            ORDER BY vt.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """)  # nosec B608

        result = await self._session.execute(sql, params)
        rows = result.fetchall()

        return [
            SemanticSearchResult(
                chunk_id=row.chunk_id,
                text_source_id=row.text_source_id,
                source_title=row.source_title,
                source_type=SourceType(row.source_type),
                reference=row.reference,
                content=row.content,
                similarity_score=float(row.similarity_score),
                metadata={
                    "surah_number": int(row.reference.split(":")[0]),
                    "verse_number": int(row.reference.split(":")[1]),
                    "translation_language": row.trans_language,
                    "translation_text": row.translation_text,
                },
            )
            for row in rows
        ]

    async def get_unembedded(
        self, language: str | None = None,
    ) -> list[VerseTranslation]:
        """Retrieve translations that do not yet have embeddings."""
        stmt = select(VerseTranslationModel).where(
            VerseTranslationModel.embedding.is_(None),
        )
        if language is not None:
            stmt = stmt.where(VerseTranslationModel.language == language)
        stmt = stmt.order_by(
            VerseTranslationModel.surah_number,
            VerseTranslationModel.verse_number,
        )
        result = await self._session.execute(stmt)
        return [_verse_trans_to_domain(m) for m in result.scalars().all()]

    async def update_embeddings_batch(
        self, updates: list[tuple[UUID, list[float], str]],
    ) -> None:
        """Store embeddings for multiple translations at once."""
        for trans_id, embedding, model_name in updates:
            await self._session.execute(
                update(VerseTranslationModel)
                .where(VerseTranslationModel.id == trans_id)
                .values(embedding=embedding, model_name=model_name)
            )
        await self._session.flush()
        logger.debug("verse_translation_embeddings_updated", count=len(updates))
