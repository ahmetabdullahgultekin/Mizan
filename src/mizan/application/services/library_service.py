"""
Library Service - manages LibrarySpace and TextSource lifecycle.
"""

from __future__ import annotations

from uuid import UUID

from mizan.domain.entities.library import LibrarySpace, TextSource
from mizan.domain.enums.library_enums import SourceType
from mizan.domain.repositories.library_interfaces import (
    ILibrarySpaceRepository,
    ITextSourceRepository,
)


class LibraryService:
    """
    Application service for managing Islamic Knowledge Library spaces
    and their text sources.
    """

    def __init__(
        self,
        space_repo: ILibrarySpaceRepository,
        source_repo: ITextSourceRepository,
    ) -> None:
        self._spaces = space_repo
        self._sources = source_repo

    # -------------------------------------------------------------------------
    # Library Space operations
    # -------------------------------------------------------------------------

    async def create_space(
        self,
        name: str,
        description: str | None = None,
    ) -> LibrarySpace:
        """Create a new library space."""
        space = LibrarySpace.create(name=name, description=description)
        return await self._spaces.create(space)

    async def get_space(self, space_id: UUID) -> LibrarySpace | None:
        """Get a library space by ID."""
        return await self._spaces.get_by_id(space_id)

    async def list_spaces(self) -> list[LibrarySpace]:
        """List all library spaces."""
        return await self._spaces.get_all()

    async def delete_space(self, space_id: UUID) -> bool:
        """Delete a library space and all its sources/chunks."""
        return await self._spaces.delete(space_id)

    # -------------------------------------------------------------------------
    # Text Source operations
    # -------------------------------------------------------------------------

    async def add_source(
        self,
        library_space_id: UUID,
        source_type: SourceType,
        title_arabic: str,
        title_turkish: str | None = None,
        title_english: str | None = None,
        author: str | None = None,
    ) -> TextSource:
        """Add a new text source to a library space."""
        space = await self._spaces.get_by_id(library_space_id)
        if space is None:
            raise ValueError(f"Library space {library_space_id} not found")

        source = TextSource.create(
            library_space_id=library_space_id,
            source_type=source_type,
            title_arabic=title_arabic,
            title_turkish=title_turkish,
            title_english=title_english,
            author=author,
        )
        return await self._sources.create(source)

    async def get_source(self, source_id: UUID) -> TextSource | None:
        """Get a text source by ID."""
        return await self._sources.get_by_id(source_id)

    async def list_sources(
        self,
        space_id: UUID,
        source_type: SourceType | None = None,
    ) -> list[TextSource]:
        """List all sources in a library space."""
        return await self._sources.get_by_space(
            space_id, source_type=source_type
        )

    async def delete_source(self, source_id: UUID) -> bool:
        """Delete a source and all its chunks."""
        return await self._sources.delete(source_id)
