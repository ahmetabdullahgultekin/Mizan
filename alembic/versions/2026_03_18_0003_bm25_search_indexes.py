"""Add tsvector columns and GIN indexes for BM25 keyword search.

Adds generated tsvector columns on `verses.text_no_tashkeel` and
`text_chunks.content` with GIN indexes to enable full-text keyword
search as a second retrieval path alongside pgvector cosine similarity.

Revision ID: 0003_bm25_search_indexes
Revises: 0002_library_and_embeddings
Create Date: 2026-03-18

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003_bm25_search_indexes"
down_revision: Union[str, None] = "0002_library_and_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # verses: Add tsvector column for full-text search on text_no_tashkeel
    # Using 'simple' config — works for Arabic (whitespace tokenization,
    # no stemming, no stop-word removal — ideal for Arabic script).
    # -------------------------------------------------------------------------
    op.execute("""
        ALTER TABLE verses
        ADD COLUMN IF NOT EXISTS text_search_vector tsvector
        GENERATED ALWAYS AS (to_tsvector('simple', COALESCE(text_no_tashkeel, ''))) STORED
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_verses_text_search_vector
        ON verses USING gin (text_search_vector)
    """)

    # -------------------------------------------------------------------------
    # text_chunks: Add tsvector column for full-text search on content
    # -------------------------------------------------------------------------
    op.execute("""
        ALTER TABLE text_chunks
        ADD COLUMN IF NOT EXISTS content_search_vector tsvector
        GENERATED ALWAYS AS (to_tsvector('simple', COALESCE(content, ''))) STORED
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_text_chunks_content_search_vector
        ON text_chunks USING gin (content_search_vector)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_text_chunks_content_search_vector")
    op.execute("ALTER TABLE text_chunks DROP COLUMN IF EXISTS content_search_vector")

    op.execute("DROP INDEX IF EXISTS ix_verses_text_search_vector")
    op.execute("ALTER TABLE verses DROP COLUMN IF EXISTS text_search_vector")
