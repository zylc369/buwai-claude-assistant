"""Add Project/Workspace/Session/Message models

Revision ID: 20260313154946
Revises: b3f184c4974c
Create Date: 2026-03-13 15:49:46

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '20260313154946'
down_revision: Union[str, Sequence[str], None] = 'b3f184c4974c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('tasks')
    op.drop_index(op.f('ix_sessions_token'), table_name='sessions')
    op.drop_table('sessions')
    op.drop_table('projects')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    op.create_table('project',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_unique_id', sa.Text(), nullable=False),
        sa.Column('worktree', sa.Text(), nullable=False),
        sa.Column('branch', sa.Text(), nullable=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('time_initialized', sa.Integer(), nullable=True),
        sa.Column('time_created', sa.Integer(), nullable=False),
        sa.Column('time_updated', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_unique_id')
    )

    op.create_table('workspace',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('workspace_unique_id', sa.Text(), nullable=False),
        sa.Column('branch', sa.Text(), nullable=True),
        sa.Column('name', sa.Text(), nullable=True),
        sa.Column('directory', sa.Text(), nullable=True),
        sa.Column('extra', sa.Text(), nullable=True),
        sa.Column('project_unique_id', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['project_unique_id'], ['project.project_unique_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('workspace_unique_id')
    )
    op.create_index('workspace_project_unique_idx', 'workspace', ['project_unique_id'])

    op.create_table('session',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_unique_id', sa.Text(), nullable=False),
        sa.Column('project_unique_id', sa.Text(), nullable=False),
        sa.Column('workspace_unique_id', sa.Text(), nullable=False),
        sa.Column('directory', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('time_created', sa.Integer(), nullable=False),
        sa.Column('time_updated', sa.Integer(), nullable=False),
        sa.Column('time_compacting', sa.Integer(), nullable=True),
        sa.Column('time_archived', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['project_unique_id'], ['project.project_unique_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_unique_id'], ['workspace.workspace_unique_id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_unique_id')
    )
    op.create_index('session_project_unique_idx', 'session', ['project_unique_id'])
    op.create_index('session_workspace_unique_idx', 'session', ['workspace_unique_id'])

    op.create_table('message',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_unique_id', sa.Text(), nullable=False),
        sa.Column('session_unique_id', sa.Text(), nullable=False),
        sa.Column('time_created', sa.Integer(), nullable=False),
        sa.Column('time_updated', sa.Integer(), nullable=False),
        sa.Column('data', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['session_unique_id'], ['session.session_unique_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_unique_id')
    )
    op.create_index('message_session_unique_idx', 'message', ['session_unique_id'])


def downgrade() -> None:
    op.drop_index('message_session_unique_idx', table_name='message')
    op.drop_table('message')

    op.drop_index('session_workspace_unique_idx', table_name='session')
    op.drop_index('session_project_unique_idx', table_name='session')
    op.drop_table('session')

    op.drop_index('workspace_project_unique_idx', table_name='workspace')
    op.drop_table('workspace')

    op.drop_table('project')

    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.create_table('projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=500), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_token'), 'sessions', ['token'], unique=True)

    op.create_table('tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('priority', sa.String(length=50), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
