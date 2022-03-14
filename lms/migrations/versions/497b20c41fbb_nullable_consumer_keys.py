"""
Allow nullable consumer keys in tables with a new application_instance_id.

Revision ID: 497b20c41fbb
Revises: 2119e1c621de
Create Date: 2022-03-24 12:55:46.664755

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "497b20c41fbb"
down_revision = "2119e1c621de"


def upgrade():
    # Allow nulls in the old consumer_key columns
    op.alter_column(
        "group_info", "consumer_key", existing_type=sa.VARCHAR(), nullable=True
    )
    op.alter_column(
        "lis_result_sourcedid",
        "oauth_consumer_key",
        existing_type=sa.TEXT(),
        nullable=True,
    )
    op.alter_column(
        "oauth2_token", "consumer_key", existing_type=sa.VARCHAR(), nullable=True
    )

    # Drop existing FK constraints
    op.drop_constraint(
        "fk__group_info__consumer_key__application_instances",
        "group_info",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk__oauth2_token__consumer_key__application_instances",
        "oauth2_token",
        type_="foreignkey",
    )

    # Adjust existing unique constraint based on consumer_key to use application_instance_id
    op.drop_constraint("uq__oauth2_token__user_id", "oauth2_token", type_="unique")
    op.drop_constraint(
        "uq__lis_result_sourcedid__oauth_consumer_key",
        "lis_result_sourcedid",
        type_="unique",
    )
    op.create_unique_constraint(
        op.f("uq__lis_result_sourcedid__application_instance_id"),
        "lis_result_sourcedid",
        ["application_instance_id", "user_id", "context_id", "resource_link_id"],
    )
    op.create_unique_constraint(
        op.f("uq__oauth2_token__user_id"),
        "oauth2_token",
        ["user_id", "application_instance_id"],
    )


def downgrade():
    op.create_foreign_key(
        "fk__oauth2_token__consumer_key__application_instances",
        "oauth2_token",
        "application_instances",
        ["consumer_key"],
        ["consumer_key"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        op.f("uq__oauth2_token__user_id"), "oauth2_token", type_="unique"
    )
    op.create_unique_constraint(
        "uq__oauth2_token__user_id", "oauth2_token", ["user_id", "consumer_key"]
    )
    op.alter_column(
        "oauth2_token", "consumer_key", existing_type=sa.VARCHAR(), nullable=False
    )
    op.drop_constraint(
        op.f("uq__lis_result_sourcedid__application_instance_id"),
        "lis_result_sourcedid",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq__lis_result_sourcedid__oauth_consumer_key",
        "lis_result_sourcedid",
        ["oauth_consumer_key", "user_id", "context_id", "resource_link_id"],
    )
    op.alter_column(
        "lis_result_sourcedid",
        "oauth_consumer_key",
        existing_type=sa.TEXT(),
        nullable=False,
    )
    op.create_foreign_key(
        "fk__group_info__consumer_key__application_instances",
        "group_info",
        "application_instances",
        ["consumer_key"],
        ["consumer_key"],
        ondelete="CASCADE",
    )
    op.alter_column(
        "group_info", "consumer_key", existing_type=sa.VARCHAR(), nullable=False
    )
