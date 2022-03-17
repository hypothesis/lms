"""
Add application_instance lti_registration relationship.

Revision ID: 2119e1c621de
Revises: aa40f7e3f053
Create Date: 2022-03-17 12:09:00.787250

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2119e1c621de"
down_revision = "aa40f7e3f053"


def upgrade():
    op.add_column(
        "application_instances",
        sa.Column("lti_registration_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "application_instances",
        sa.Column("deployment_id", sa.UnicodeText(), nullable=True),
    )
    op.alter_column(
        "application_instances",
        "consumer_key",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.create_unique_constraint(
        op.f("uq__application_instances__lti_registration_id"),
        "application_instances",
        ["lti_registration_id", "deployment_id"],
    )
    op.create_foreign_key(
        op.f("fk__application_instances__lti_registration_id__lti_registration"),
        "application_instances",
        "lti_registration",
        ["lti_registration_id"],
        ["id"],
        ondelete="cascade",
    )
    op.create_check_constraint(
        "consumer_key_required_for_lti_11",
        table_name="application_instances",
        condition="""(consumer_key IS NULL AND lti_registration_id IS NOT NULL and deployment_id IS NOT NULL)
        OR (consumer_key IS NOT NULL)
        """,
    )


def downgrade():
    op.drop_constraint(
        op.f("fk__application_instances__lti_registration_id__lti_registration"),
        "application_instances",
        type_="foreignkey",
    )
    op.drop_constraint(
        op.f("uq__application_instances__lti_registration_id"),
        "application_instances",
        type_="unique",
    )
    op.alter_column(
        "application_instances",
        "consumer_key",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
    op.drop_column("application_instances", "deployment_id")
    op.drop_column("application_instances", "lti_registration_id")
