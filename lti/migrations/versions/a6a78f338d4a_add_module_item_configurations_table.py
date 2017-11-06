"""
add module_item_configurations table

Revision ID: a6a78f338d4a
Revises: d9e4bc3797b3
Create Date: 2017-11-06 10:11:17.068452

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a6a78f338d4a'
down_revision = 'd9e4bc3797b3'


def upgrade():
    op.create_table(
      'module_item_configurations',
      sa.Column('id', sa.Integer, autoincrement=True, primary_key=True),
      sa.Column('document_url', sa.String),
      sa.Column('resource_link_id', sa.String),
      sa.Column('tool_consumer_instance_guid', sa.String)
    )


def downgrade():
    pass
