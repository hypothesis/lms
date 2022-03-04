"""
Bakfill application_instance_id in group_info, lis_result_sourcedid and oauth2_token.

Revision ID: 0a3bfcc14133
Revises: 407ff423b9e3
Create Date: 2022-03-04 11:39:06.573269

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0a3bfcc14133"
down_revision = "407ff423b9e3"


def upgrade():
    conn = op.get_bind()
    # Fist backfill the new application_instance_id columns based on the existing consumer_key columns
    conn.execute(
        """
            UPDATE group_info
                set application_instance_id = application_instances.id
                from application_instances
                where application_instances.consumer_key = group_info.consumer_key and application_instance_id is null
        """
    )
    conn.execute(
        """
            UPDATE lis_result_sourcedid
                set application_instance_id = application_instances.id
                from application_instances
                where application_instances.consumer_key = lis_result_sourcedid.oauth_consumer_key and application_instance_id is null
        """
    )
    conn.execute(
        """
            UPDATE oauth2_token
                set application_instance_id = application_instances.id
                from application_instances
                where application_instances.consumer_key = oauth2_token.consumer_key and application_instance_id is null
        """
    )

    # Mark application_instance_id as non nullable
    op.alter_column(
        "group_info",
        "application_instance_id",
        existing_type=sa.INTEGER(),
        nullable=False,
    )
    op.alter_column(
        "lis_result_sourcedid",
        "application_instance_id",
        existing_type=sa.INTEGER(),
        nullable=False,
    )

    op.alter_column(
        "oauth2_token",
        "application_instance_id",
        existing_type=sa.INTEGER(),
        nullable=False,
    )


def downgrade():
    op.alter_column(
        "oauth2_token",
        "application_instance_id",
        existing_type=sa.INTEGER(),
        nullable=True,
    )
    op.alter_column(
        "lis_result_sourcedid",
        "application_instance_id",
        existing_type=sa.INTEGER(),
        nullable=True,
    )
    op.alter_column(
        "group_info",
        "application_instance_id",
        existing_type=sa.INTEGER(),
        nullable=True,
    )
