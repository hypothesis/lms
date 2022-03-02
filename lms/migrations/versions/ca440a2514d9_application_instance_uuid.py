"""
Adds application_instance.uuid.

Revision ID: ca440a2514d9
Revises: 7a4812876915
Create Date: 2022-03-02 12:39:51.591719

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ca440a2514d9"
down_revision = "7a4812876915"


def upgrade():
    op.add_column(
        "application_instances",
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_unique_constraint(
        op.f("uq__application_instances__uuid"), "application_instances", ["uuid"]
    )


def downgrade():
    op.drop_constraint(
        op.f("uq__application_instances__uuid"), "application_instances", type_="unique"
    )
    op.drop_column("application_instances", "uuid")
