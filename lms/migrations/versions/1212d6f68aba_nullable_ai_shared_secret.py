"""
nullable_ai_shared_secret

Revision ID: 1212d6f68aba
Revises: 911d1f7da759
Create Date: 2022-05-20 10:00:36.518760

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1212d6f68aba"
down_revision = "911d1f7da759"


def upgrade():
    op.alter_column(
        "application_instances",
        "shared_secret",
        existing_type=sa.VARCHAR(),
        nullable=True,
    )
    op.drop_constraint(
        op.f("ck__application_instances__consumer_key_required_for_lti_11"),
        "application_instances",
        type_="check",
    )

    op.create_check_constraint(
        "lti_required_columns",
        table_name="application_instances",
        condition="""(lti_registration_id IS NOT NULL and deployment_id IS NOT NULL)
        OR (consumer_key IS NOT NULL AND shared_secret IS NOT NULL)
        """,
    )


def downgrade():
    op.drop_constraint(
        op.f("ck__application_instances__lti_required_columns"),
        "application_instances",
        type_="check",
    )

    op.create_check_constraint(
        "consumer_key_required_for_lti_11",
        table_name="application_instances",
        condition="""(consumer_key IS NULL AND lti_registration_id IS NOT NULL and deployment_id IS NOT NULL)
        OR (consumer_key IS NOT NULL)
        """,
    )

    op.alter_column(
        "application_instances",
        "shared_secret",
        existing_type=sa.VARCHAR(),
        nullable=False,
    )
