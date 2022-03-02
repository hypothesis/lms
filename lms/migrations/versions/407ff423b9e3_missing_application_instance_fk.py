"""
Add missing application_instances FK.

Revision ID: 407ff423b9e3
Revises: 7a4812876915
Create Date: 2022-03-03 16:45:18.847715

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "407ff423b9e3"
down_revision = "7a4812876915"


def upgrade():
    # Add the new column as nullable
    op.add_column(
        "group_info", sa.Column("application_instance_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "lis_result_sourcedid",
        sa.Column("application_instance_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "oauth2_token",
        sa.Column("application_instance_id", sa.Integer(), nullable=True),
    )

    # Create PK indexes for all of them
    op.create_foreign_key(
        op.f("fk__group_info__application_instance_id__application_instances"),
        "group_info",
        "application_instances",
        ["application_instance_id"],
        ["id"],
        ondelete="cascade",
    )
    op.create_foreign_key(
        op.f(
            "fk__lis_result_sourcedid__application_instance_id__application_instances"
        ),
        "lis_result_sourcedid",
        "application_instances",
        ["application_instance_id"],
        ["id"],
        ondelete="cascade",
    )
    op.create_foreign_key(
        op.f("fk__oauth2_token__application_instance_id__application_instances"),
        "oauth2_token",
        "application_instances",
        ["application_instance_id"],
        ["id"],
        ondelete="cascade",
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__oauth2_token__application_instance_id__application_instances"),
        "oauth2_token",
        type_="foreignkey",
    )
    op.drop_column("oauth2_token", "application_instance_id")
    op.drop_constraint(
        op.f(
            "fk__lis_result_sourcedid__application_instance_id__application_instances"
        ),
        "lis_result_sourcedid",
        type_="foreignkey",
    )
    op.drop_column("lis_result_sourcedid", "application_instance_id")
    op.drop_constraint(
        op.f("fk__group_info__application_instance_id__application_instances"),
        "group_info",
        type_="foreignkey",
    )
    op.drop_column("group_info", "application_instance_id")
