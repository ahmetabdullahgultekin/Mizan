"""
Library Management API Endpoints.

Manage Islamic Knowledge Library spaces and text sources.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from mizan.api.dependencies import DbSession, verify_api_key
from mizan.application.dtos.library_requests import (
    AddTextSourceRequest,
    CreateLibrarySpaceRequest,
)
from mizan.application.dtos.library_responses import (
    LibrarySpaceResponse,
    TextSourceResponse,
)
from mizan.application.services.indexing_service import IndexingService
from mizan.application.services.library_service import LibraryService
from mizan.domain.enums.library_enums import SourceType
from mizan.infrastructure.config import get_settings
from mizan.infrastructure.embeddings.factory import get_embedding_service
from mizan.infrastructure.persistence.library_repositories import (
    PostgresLibrarySpaceRepository,
    PostgresTextChunkRepository,
    PostgresTextSourceRepository,
)

router = APIRouter(prefix="/library")


def _get_library_service(session: DbSession) -> LibraryService:
    return LibraryService(
        space_repo=PostgresLibrarySpaceRepository(session),
        source_repo=PostgresTextSourceRepository(session),
    )


def _get_indexing_service(session: DbSession) -> IndexingService:
    settings = get_settings()
    return IndexingService(
        source_repo=PostgresTextSourceRepository(session),
        chunk_repo=PostgresTextChunkRepository(session),
        embedding_service=get_embedding_service(),
        batch_size=settings.embedding_batch_size,
    )


# ---------------------------------------------------------------------------
# Library Space endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/spaces",
    response_model=LibrarySpaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new library space",
)
async def create_library_space(
    body: CreateLibrarySpaceRequest,
    session: DbSession,
    _: None = Depends(verify_api_key),
) -> LibrarySpaceResponse:
    """
    Create a named collection to organize Islamic text sources.

    Example: 'Mizan Ana Kütüphanesi' to hold Quran texts, tafsir, and hadith.
    """
    svc = _get_library_service(session)
    space = await svc.create_space(name=body.name, description=body.description)
    return LibrarySpaceResponse(
        id=space.id,
        name=space.name,
        description=space.description,
        created_at=space.created_at,
    )


@router.get(
    "/spaces",
    response_model=list[LibrarySpaceResponse],
    summary="List all library spaces",
)
async def list_library_spaces(session: DbSession) -> list[LibrarySpaceResponse]:
    """List all Islamic Knowledge Library spaces."""
    svc = _get_library_service(session)
    spaces = await svc.list_spaces()
    return [
        LibrarySpaceResponse(
            id=s.id,
            name=s.name,
            description=s.description,
            created_at=s.created_at,
        )
        for s in spaces
    ]


@router.get(
    "/spaces/{space_id}",
    response_model=LibrarySpaceResponse,
    summary="Get a library space",
)
async def get_library_space(space_id: UUID, session: DbSession) -> LibrarySpaceResponse:
    """Get details of a specific library space."""
    svc = _get_library_service(session)
    space = await svc.get_space(space_id)
    if space is None:
        raise HTTPException(status_code=404, detail=f"Library space {space_id} not found")
    return LibrarySpaceResponse(
        id=space.id,
        name=space.name,
        description=space.description,
        created_at=space.created_at,
    )


@router.delete(
    "/spaces/{space_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a library space",
)
async def delete_library_space(space_id: UUID, session: DbSession, _: None = Depends(verify_api_key)) -> None:
    """Delete a library space and all its sources and chunks."""
    svc = _get_library_service(session)
    found = await svc.delete_space(space_id)
    if not found:
        raise HTTPException(status_code=404, detail=f"Library space {space_id} not found")


# ---------------------------------------------------------------------------
# Text Source endpoints
# ---------------------------------------------------------------------------


def _source_to_response(source: object) -> TextSourceResponse:
    from mizan.domain.entities.library import TextSource
    s: TextSource = source  # type: ignore[assignment]
    return TextSourceResponse(
        id=s.id,
        library_space_id=s.library_space_id,
        source_type=s.source_type,
        title_arabic=s.title_arabic,
        title_turkish=s.title_turkish,
        title_english=s.title_english,
        author=s.author,
        status=s.status,
        total_chunks=s.total_chunks,
        indexed_chunks=s.indexed_chunks,
        indexing_progress=s.indexing_progress,
        embedding_model=s.embedding_model,
        created_at=s.created_at,
        updated_at=s.updated_at,
    )


@router.post(
    "/spaces/{space_id}/sources",
    response_model=TextSourceResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Add a text source and start indexing",
)
async def add_text_source(
    space_id: UUID,
    body: AddTextSourceRequest,
    background_tasks: BackgroundTasks,
    session: DbSession,
    _: None = Depends(verify_api_key),
) -> TextSourceResponse:
    """
    Add an Islamic text source to a library and trigger background indexing.

    The source is created immediately (status=PENDING), and indexing
    runs as a background task. Poll the source's status endpoint to
    monitor progress.

    **Source types and chunking:**
    - QURAN: verse by verse (use with VerseChunker via scripts/embed_quran.py)
    - TAFSIR: paragraph-based (~300 words)
    - HADITH: paragraph-based (~200 words)
    - OTHER: sliding window (200 words, 50 overlap)
    """
    lib_svc = _get_library_service(session)
    source = await lib_svc.add_source(
        library_space_id=space_id,
        source_type=body.source_type,
        title_arabic=body.title_arabic,
        title_turkish=body.title_turkish,
        title_english=body.title_english,
        author=body.author,
    )

    # Kick off indexing in background
    idx_svc = _get_indexing_service(session)
    background_tasks.add_task(
        idx_svc.index_text_source,
        source.id,
        body.content,
        body.source_type,
    )

    return _source_to_response(source)


@router.get(
    "/sources/{source_id}",
    response_model=TextSourceResponse,
    summary="Get text source status",
)
async def get_text_source(source_id: UUID, session: DbSession) -> TextSourceResponse:
    """Get a text source with its current indexing status and progress."""
    lib_svc = _get_library_service(session)
    source = await lib_svc.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail=f"Text source {source_id} not found")
    return _source_to_response(source)


@router.get(
    "/spaces/{space_id}/sources",
    response_model=list[TextSourceResponse],
    summary="List sources in a library space",
)
async def list_text_sources(
    space_id: UUID,
    session: DbSession,
    source_type: SourceType | None = None,
) -> list[TextSourceResponse]:
    """List all text sources in a library space, optionally filtered by type."""
    lib_svc = _get_library_service(session)
    sources = await lib_svc.list_sources(space_id, source_type=source_type)
    return [_source_to_response(s) for s in sources]


@router.delete(
    "/sources/{source_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a text source",
)
async def delete_text_source(source_id: UUID, session: DbSession, _: None = Depends(verify_api_key)) -> None:
    """Delete a text source and all its chunks and embeddings."""
    lib_svc = _get_library_service(session)
    found = await lib_svc.delete_source(source_id)
    if not found:
        raise HTTPException(status_code=404, detail=f"Text source {source_id} not found")
