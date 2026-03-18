"""Add verse_translations table for cross-lingual semantic search.

Stores English and Turkish verse translations with pgvector embeddings
so that same-language queries (e.g. "patience to parents") match directly
against translation text rather than relying on cross-lingual bridging.

Revision ID: 0004_verse_translations
Revises: 0003_bm25_search_indexes
Create Date: 2026-03-18

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004_verse_translations"
down_revision: Union[str, None] = "0003_bm25_search_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE verse_translations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            verse_id UUID NOT NULL REFERENCES verses(id),
            surah_number INTEGER NOT NULL,
            verse_number INTEGER NOT NULL,
            language VARCHAR(10) NOT NULL,
            translation_text TEXT NOT NULL,
            source_name VARCHAR(200) NOT NULL,
            resource_id INTEGER NOT NULL,
            embedding VECTOR(768),
            model_name VARCHAR(200),
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)

    # Unique: one translation per verse per language per source
    op.execute("""
        ALTER TABLE verse_translations ADD CONSTRAINT uq_verse_translation
            UNIQUE (verse_id, language, resource_id)
    """)

    # HNSW index for vector search
    op.execute("""
        CREATE INDEX ix_verse_translations_embedding ON verse_translations
            USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)
    """)

    # Lookup indexes
    op.execute("""
        CREATE INDEX ix_verse_translations_location
            ON verse_translations (surah_number, verse_number)
    """)

    op.execute("""
        CREATE INDEX ix_verse_translations_language
            ON verse_translations (language)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_verse_translations_language")
    op.execute("DROP INDEX IF EXISTS ix_verse_translations_location")
    op.execute("DROP INDEX IF EXISTS ix_verse_translations_embedding")
    op.execute("DROP TABLE IF EXISTS verse_translations")
