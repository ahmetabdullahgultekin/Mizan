"""Initial schema - Surahs, Verses, Morphology tables.

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create extension for trigram search
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Create surahs table
    op.create_table(
        "surahs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name_arabic", sa.String(length=100), nullable=False),
        sa.Column("name_english", sa.String(length=100), nullable=False),
        sa.Column("name_transliteration", sa.String(length=100), nullable=False),
        sa.Column("revelation_type", sa.String(length=20), nullable=False),
        sa.Column("revelation_order", sa.Integer(), nullable=False),
        sa.Column("basmalah_status", sa.String(length=30), nullable=False),
        sa.Column("verse_count", sa.Integer(), nullable=False),
        sa.Column("ruku_count", sa.Integer(), nullable=False),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("letter_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("abjad_value", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_surahs_revelation_type", "surahs", ["revelation_type"])
    op.create_index("ix_surahs_revelation_order", "surahs", ["revelation_order"])

    # Create verses table
    op.create_table(
        "verses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("surah_number", sa.Integer(), nullable=False),
        sa.Column("verse_number", sa.Integer(), nullable=False),
        sa.Column("text_uthmani", sa.Text(), nullable=False),
        sa.Column("text_uthmani_min", sa.Text(), nullable=True),
        sa.Column("text_simple", sa.Text(), nullable=True),
        sa.Column("text_normalized_full", sa.Text(), nullable=False),
        sa.Column("text_no_tashkeel", sa.Text(), nullable=False),
        sa.Column("qiraat_variants", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("juz_number", sa.Integer(), nullable=False),
        sa.Column("hizb_number", sa.Integer(), nullable=False),
        sa.Column("ruku_number", sa.Integer(), nullable=False),
        sa.Column("manzil_number", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("is_sajdah", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("sajdah_type", sa.String(length=20), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=False),
        sa.Column("letter_count", sa.Integer(), nullable=False),
        sa.Column("abjad_value_mashriqi", sa.Integer(), nullable=False),
        sa.Column("abjad_value_maghribi", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["surah_number"], ["surahs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("surah_number", "verse_number", name="uq_verse_location"),
    )
    op.create_index("ix_verses_surah_verse", "verses", ["surah_number", "verse_number"])
    op.create_index("ix_verses_juz", "verses", ["juz_number"])
    op.create_index("ix_verses_hizb", "verses", ["hizb_number"])
    op.create_index("ix_verses_manzil", "verses", ["manzil_number"])
    op.create_index("ix_verses_page", "verses", ["page_number"])
    op.create_index("ix_verses_sajdah", "verses", ["is_sajdah"])
    op.create_index(
        "ix_verses_text_normalized",
        "verses",
        ["text_normalized_full"],
        postgresql_using="gin",
        postgresql_ops={"text_normalized_full": "gin_trgm_ops"},
    )

    # Create morphology table
    op.create_table(
        "morphology",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("surah_number", sa.Integer(), nullable=False),
        sa.Column("verse_number", sa.Integer(), nullable=False),
        sa.Column("word_number", sa.Integer(), nullable=False),
        sa.Column("segment_number", sa.Integer(), nullable=False),
        sa.Column("verse_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("word_uthmani", sa.String(length=100), nullable=False),
        sa.Column("word_imlaei", sa.String(length=100), nullable=False),
        sa.Column("segment_uthmani", sa.String(length=50), nullable=True),
        sa.Column("segment_imlaei", sa.String(length=50), nullable=True),
        sa.Column("morpheme_type", sa.String(length=20), nullable=False),
        sa.Column("pos_tag", sa.String(length=20), nullable=False),
        sa.Column("root", sa.String(length=20), nullable=True),
        sa.Column("lemma", sa.String(length=50), nullable=True),
        sa.Column("pattern", sa.String(length=30), nullable=True),
        sa.Column("person", sa.String(length=5), nullable=True),
        sa.Column("gender", sa.String(length=5), nullable=True),
        sa.Column("number", sa.String(length=5), nullable=True),
        sa.Column("case_state", sa.String(length=20), nullable=True),
        sa.Column("mood_voice", sa.String(length=20), nullable=True),
        sa.Column("syntactic_role", sa.String(length=50), nullable=True),
        sa.Column("irab_description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["verse_id"], ["verses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_morphology_location", "morphology", ["surah_number", "verse_number", "word_number"])
    op.create_index("ix_morphology_root", "morphology", ["root"])
    op.create_index("ix_morphology_lemma", "morphology", ["lemma"])
    op.create_index("ix_morphology_pos", "morphology", ["pos_tag"])
    op.create_index("ix_morphology_verse_id", "morphology", ["verse_id"])


def downgrade() -> None:
    op.drop_table("morphology")
    op.drop_table("verses")
    op.drop_table("surahs")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
