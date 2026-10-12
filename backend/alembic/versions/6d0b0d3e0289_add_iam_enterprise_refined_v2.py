"""add_iam_enterprise_refined_v2

Revision ID: 6d0b0d3e0289
Revises: 
Create Date: 2026-07-15 21:47:17.414734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6d0b0d3e0289'
down_revision: Union[str, Sequence[str], None] = '0001_initial_base_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if 'audit_logs' not in existing_tables:
        op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(), nullable=False),
        sa.Column('request_id', sa.String(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_audit_logs_event_id'), 'audit_logs', ['event_id'], unique=True)
        op.create_index(op.f('ix_audit_logs_event_type'), 'audit_logs', ['event_type'], unique=False)
        op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
        op.create_index(op.f('ix_audit_logs_request_id'), 'audit_logs', ['request_id'], unique=False)
        op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
        op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)

    if 'user_sessions' not in existing_tables:
        op.create_table('user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('refresh_token_jti', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('device_name', sa.String(), nullable=True),
        sa.Column('browser', sa.String(), nullable=True),
        sa.Column('operating_system', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_sessions_expires_at'), 'user_sessions', ['expires_at'], unique=False)
        op.create_index(op.f('ix_user_sessions_id'), 'user_sessions', ['id'], unique=False)
        op.create_index(op.f('ix_user_sessions_refresh_token_jti'), 'user_sessions', ['refresh_token_jti'], unique=True)
        op.create_index(op.f('ix_user_sessions_status'), 'user_sessions', ['status'], unique=False)
        op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)

    if 'users' in existing_tables:
        existing_cols = {col['name'] for col in inspector.get_columns('users')}
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('users')}
        existing_checks = {chk['name'] for chk in inspector.get_check_constraints('users')}

        if 'role' not in existing_cols:
            op.add_column('users', sa.Column('role', sa.String(), nullable=False, server_default='USER'))
        if 'is_verified' not in existing_cols:
            op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
        if 'verification_token_hash' not in existing_cols:
            op.add_column('users', sa.Column('verification_token_hash', sa.String(), nullable=True))
        if 'verification_token_expiry' not in existing_cols:
            op.add_column('users', sa.Column('verification_token_expiry', sa.DateTime(), nullable=True))
        if 'password_reset_token_hash' not in existing_cols:
            op.add_column('users', sa.Column('password_reset_token_hash', sa.String(), nullable=True))
        if 'password_reset_token_expiry' not in existing_cols:
            op.add_column('users', sa.Column('password_reset_token_expiry', sa.DateTime(), nullable=True))
        if 'login_attempts' not in existing_cols:
            op.add_column('users', sa.Column('login_attempts', sa.Integer(), nullable=False, server_default='0'))
        if 'locked_until' not in existing_cols:
            op.add_column('users', sa.Column('locked_until', sa.DateTime(), nullable=True))

        if op.f('ix_users_is_verified') not in existing_indexes and 'ix_users_is_verified' not in existing_indexes:
            op.create_index(op.f('ix_users_is_verified'), 'users', ['is_verified'], unique=False)
        if op.f('ix_users_locked_until') not in existing_indexes and 'ix_users_locked_until' not in existing_indexes:
            op.create_index(op.f('ix_users_locked_until'), 'users', ['locked_until'], unique=False)
        if op.f('ix_users_password_reset_token_hash') not in existing_indexes and 'ix_users_password_reset_token_hash' not in existing_indexes:
            op.create_index(op.f('ix_users_password_reset_token_hash'), 'users', ['password_reset_token_hash'], unique=True)
        if op.f('ix_users_role') not in existing_indexes and 'ix_users_role' not in existing_indexes:
            op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
        if op.f('ix_users_verification_token_hash') not in existing_indexes and 'ix_users_verification_token_hash' not in existing_indexes:
            op.create_index(op.f('ix_users_verification_token_hash'), 'users', ['verification_token_hash'], unique=True)

        if 'chk_login_attempts_positive' not in existing_checks:
            op.create_check_constraint("chk_login_attempts_positive", "users", "login_attempts >= 0")
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("chk_login_attempts_positive", "users")
    op.drop_index(op.f('ix_users_verification_token_hash'), table_name='users')
    op.drop_index(op.f('ix_users_role'), table_name='users')
    op.drop_index(op.f('ix_users_password_reset_token_hash'), table_name='users')
    op.drop_index(op.f('ix_users_locked_until'), table_name='users')
    op.drop_index(op.f('ix_users_is_verified'), table_name='users')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'login_attempts')
    op.drop_column('users', 'password_reset_token_expiry')
    op.drop_column('users', 'password_reset_token_hash')
    op.drop_column('users', 'verification_token_expiry')
    op.drop_column('users', 'verification_token_hash')
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'role')
    op.drop_index(op.f('ix_user_sessions_user_id'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_status'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_refresh_token_jti'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_id'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_expires_at'), table_name='user_sessions')
    op.drop_table('user_sessions')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_request_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_event_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_event_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    # ### end Alembic commands ###
