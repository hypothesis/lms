"""
Creates an unique index on grouping.authority_provided_id.

Revision ID: 69265d3e6ffe
Revises: 6882c201b56e
Create Date: 2022-01-26 11:18:46.851084

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "69265d3e6ffe"
down_revision = "6882c201b56e"


def upgrade():
    op.create_index(
        op.f("ix__grouping_authority_provided_id"),
        "grouping",
        ["authority_provided_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(op.f("ix__grouping_authority_provided_id"), table_name="grouping")
