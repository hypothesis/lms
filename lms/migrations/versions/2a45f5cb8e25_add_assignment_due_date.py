"""add_assignment_due_date

Revision ID: 2a45f5cb8e25
Revises: af090ca7e73f
"""
from alembic import op
import sqlalchemy as sa


revision = '2a45f5cb8e25'
down_revision = 'af090ca7e73f'


def upgrade() -> None:
    op.add_column('assignment', sa.Column('due_date', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('assignment', 'due_date')
