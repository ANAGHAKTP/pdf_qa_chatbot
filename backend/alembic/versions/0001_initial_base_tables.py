"""initial_base_tables

Revision ID: 0001_initial_base_tables
Revises: 
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_base_tables'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    # 1. users
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('hashed_password', sa.String(), nullable=False),
            sa.Column('full_name', sa.String(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
            sa.Column('is_admin', sa.Boolean(), server_default=sa.text('false'), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
        op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. folders
    if 'folders' not in existing_tables:
        op.create_table(
            'folders',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('parent_id', sa.Integer(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['parent_id'], ['folders.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_folders_id'), 'folders', ['id'], unique=False)

    # 3. documents
    if 'documents' not in existing_tables:
        op.create_table(
            'documents',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('filename', sa.String(), nullable=False),
            sa.Column('filepath', sa.String(), nullable=False),
            sa.Column('file_size', sa.Integer(), nullable=False),
            sa.Column('chunk_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('status', sa.String(), server_default='indexing', nullable=False),
            sa.Column('s3_key', sa.String(), nullable=True),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('folder_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['folder_id'], ['folders.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)

    # 4. chat_sessions
    if 'chat_sessions' not in existing_tables:
        op.create_table(
            'chat_sessions',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # 5. chat_messages
    if 'chat_messages' not in existing_tables:
        op.create_table(
            'chat_messages',
            sa.Column('id', sa.String(), nullable=False),
            sa.Column('session_id', sa.String(), nullable=False),
            sa.Column('role', sa.String(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('citations', sa.JSON(), nullable=True),
            sa.Column('embedding_time_ms', sa.Float(), nullable=True),
            sa.Column('retrieval_time_ms', sa.Float(), nullable=True),
            sa.Column('llm_time_ms', sa.Float(), nullable=True),
            sa.Column('total_time_ms', sa.Float(), nullable=True),
            sa.Column('token_count', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # 6. feedbacks
    if 'feedbacks' not in existing_tables:
        op.create_table(
            'feedbacks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('message_id', sa.String(), nullable=False),
            sa.Column('rating', sa.Integer(), nullable=False),
            sa.Column('comment', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_feedbacks_id'), 'feedbacks', ['id'], unique=False)

    # 7. analytics
    if 'analytics' not in existing_tables:
        op.create_table(
            'analytics',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('action', sa.String(), nullable=False),
            sa.Column('endpoint', sa.String(), nullable=True),
            sa.Column('status_code', sa.Integer(), nullable=True),
            sa.Column('response_time_ms', sa.Float(), nullable=True),
            sa.Column('token_usage', sa.Integer(), nullable=True),
            sa.Column('metadata_json', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_analytics_id'), 'analytics', ['id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'analytics' in existing_tables:
        op.drop_index(op.f('ix_analytics_id'), table_name='analytics')
        op.drop_table('analytics')

    if 'feedbacks' in existing_tables:
        op.drop_index(op.f('ix_feedbacks_id'), table_name='feedbacks')
        op.drop_table('feedbacks')

    if 'chat_messages' in existing_tables:
        op.drop_table('chat_messages')

    if 'chat_sessions' in existing_tables:
        op.drop_table('chat_sessions')

    if 'documents' in existing_tables:
        op.drop_index(op.f('ix_documents_id'), table_name='documents')
        op.drop_table('documents')

    if 'folders' in existing_tables:
        op.drop_index(op.f('ix_folders_id'), table_name='folders')
        op.drop_table('folders')

    if 'users' in existing_tables:
        op.drop_index(op.f('ix_users_email'), table_name='users')
        op.drop_index(op.f('ix_users_id'), table_name='users')
        op.drop_table('users')
