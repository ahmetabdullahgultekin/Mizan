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
)
from mizan.domain.enums.library_enums import IndexingStatus, SourceType
from mizan.domain.repositories.library_interfaces import (
    ILibrarySpaceRepository,
    ITextChunkRepository,
    ITextSourceRepository,
    IVerseEmbeddingRepository,
)
from mizan.infrastructure.persistence.models import (
    LibrarySpaceModel,
    TextChunkModel,
    TextSourceModel,
    VerseEmbeddingModel,
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
        found = result.rowcount > 0
        logger.info("library_space_deleted", space_id=str(space_id), found=found)
        return found


# ---------------------------------------------------------------------------
# TextSource Repository
# ---------------------------------------------------------------------------


class PostgresTextSourceRepository(ITextSourceRepository):
    """PostgreSQL-backed text source repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, source: TextSource) -> TextSource:  # type: ignore[override]
        logger.info("text_source_creating", source_id=str(source.id), source_type=source.source_type.value)
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
        stmt = select(TextSourceModel).where(
            TextSourceModel.library_space_id == space_id
        )
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
        values: dict = {
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
            update(TextSourceModel)
            .where(TextSourceModel.id == source_id)
            .values(**values)
        )
        await self._session.flush()
        return await self.get_by_id(source_id)

    async def delete(self, source_id: UUID) -> bool:
        result = await self._session.execute(
            delete(TextSourceModel).where(TextSourceModel.id == source_id)
        )
        return result.rowcount > 0


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
            update(TextChunkModel)
            .where(TextChunkModel.id == chunk_id)
            .values(embedding=embedding)
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
        params: dict = {"embedding": str(clean_embedding), "limit": limit}

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
            where_clauses.append(
                f"(tc.embedding <=> CAST(:embedding AS vector)) < {max_distance}"
            )

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

    async def delete_by_source(self, source_id: UUID) -> int:
        result = await self._session.execute(
            delete(TextChunkModel).where(
                TextChunkModel.text_source_id == source_id
            )
        )
        return result.rowcount


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
        params: dict = {"embedding": str(clean_embedding), "limit": limit}

        if exclude_surah is not None and exclude_verse is not None:
            where_clauses.append(
                "NOT (surah_number = :excl_surah AND verse_number = :excl_verse)"
            )
            params["excl_surah"] = exclude_surah
            params["excl_verse"] = exclude_verse

        where_sql = (
            "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        )

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
        params: dict = {"embedding": str(clean_embedding), "limit": limit}

        where_clauses = ["ve.embedding IS NOT NULL"]

        if min_similarity > 0:
            max_distance = 1.0 - min_similarity
            where_clauses.append(
                f"(ve.embedding <=> CAST(:embedding AS vector)) < {max_distance}"
            )

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

    async def get_total_count(self, model_name: str | None = None) -> int:
        from sqlalchemy import func

        stmt = select(func.count()).select_from(VerseEmbeddingModel)
        if model_name:
            stmt = stmt.where(VerseEmbeddingModel.model_name == model_name)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_embedded_verse_keys(
        self, model_name: str | None = None
    ) -> set[tuple[int, int]]:
        """Return a set of (surah_number, verse_number) for already-embedded verses.

        Used by embed_quran.py to skip verses that already have embeddings,
        enabling checkpoint/resume on interrupted embedding runs.
        """
        stmt = select(VerseEmbeddingModel.surah_number, VerseEmbeddingModel.verse_number)
        if model_name:
            stmt = stmt.where(VerseEmbeddingModel.model_name == model_name)
        result = await self._session.execute(stmt)
        return {(int(row.surah_number), int(row.verse_number)) for row in result.fetchall()}
