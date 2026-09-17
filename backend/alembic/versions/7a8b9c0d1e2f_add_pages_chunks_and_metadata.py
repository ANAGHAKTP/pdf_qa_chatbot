"""add_pages_chunks_and_metadata

Revision ID: 7a8b9c0d1e2f
Revises: 6d0b0d3e0289
Create Date: 2026-09-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7a8b9c0d1e2f'
down_revision: Union[str, Sequence[str], None] = '6d0b0d3e0289'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add doc_metadata JSON column to documents table
    op.add_column('documents', sa.Column('doc_metadata', sa.JSON(), nullable=True))

    # 2. Create document_pages table
    op.create_table(
        'document_pages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_id', sa.Integer(), nullable=False),
        sa.Column('page_num', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint('page_num >= 1', name='chk_page_num_positive'),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('doc_id', 'page_num', name='uq_document_pages_doc_id_page_num')
    )
    op.create_index(op.f('ix_document_pages_doc_id'), 'document_pages', ['doc_id'], unique=False)
    op.create_index(op.f('ix_document_pages_id'), 'document_pages', ['id'], unique=False)

    # 3. Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('doc_id', sa.Integer(), nullable=False),
        sa.Column('page', sa.Integer(), nullable=False),
        sa.Column('chunk_idx', sa.Integer(), nullable=False),
        sa.Column('chunk_id', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_section', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['doc_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_chunks_chunk_id'), 'document_chunks', ['chunk_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_doc_id'), 'document_chunks', ['doc_id'], unique=False)
    op.create_index(op.f('ix_document_chunks_id'), 'document_chunks', ['id'], unique=False)

    # 4. Create GIN index on search_vector column for PostgreSQL Full-Text Search
    op.create_index('ik_document_chunks_search_vector', 'document_chunks', ['search_vector'], postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('ik_document_chunks_search_vector', table_name='document_chunks', postgresql_using='gin')
    op.drop_index(op.f('ix_document_chunks_id'), table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_doc_id'), table_name='document_chunks')
    op.drop_index(op.f('ix_document_chunks_chunk_id'), table_name='document_chunks')
    op.drop_table('document_chunks')

    op.drop_index(op.f('ix_document_pages_id'), table_name='document_pages')
    op.drop_index(op.f('ix_document_pages_doc_id'), table_name='document_pages')
    op.drop_table('document_pages')

    op.drop_column('documents', 'doc_metadata')
