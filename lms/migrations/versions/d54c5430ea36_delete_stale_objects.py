"""
Delete stale DB objects that were removed from the DB not using alembic.

This migration was added retroactively in alambic's history as it only affects
local setups and we don't want to run it in production.

Revision ID: d54c5430ea36
Revises: edab0e4610e0
Create Date: 2021-06-16 10:14:09.764318

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d54c5430ea36"
down_revision = "edab0e4610e0"


def upgrade():
    op.drop_table("oauth2_unvalidated_credentials")
    op.drop_constraint(
        "fk__lis_result_sourcedid__oauth_consumer_key__applicati_7fc0",
        "lis_result_sourcedid",
        type_="foreignkey",
    )


def downgrade():
    op.create_foreign_key(
        "fk__lis_result_sourcedid__oauth_consumer_key__applicati_7fc0",
        "lis_result_sourcedid",
        "application_instances",
        ["oauth_consumer_key"],
        ["consumer_key"],
    )
    op.create_table(
        "oauth2_unvalidated_credentials",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column("client_secret", sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column(
            "authorization_server", sa.TEXT(), autoincrement=False, nullable=True
        ),
        sa.Column("email_address", sa.TEXT(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk__oauth2_unvalidated_credentials"),
    )
