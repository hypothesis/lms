"""
Add User model

Revision ID: 1ef005129263
Revises: 58f2693de313
Create Date: 2017-11-21 14:18:08.548852

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1ef005129263'
down_revision = '58f2693de313'


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, autoincrement=True, primary_key=True),
        sa.Column('name', sa.Text, nullable=False, unique=True),
        sa.Column('password_hash', sa.Text),
        sa.Column('salt', sa.Text)
    )


def downgrade():
    op.drop_table('users')
