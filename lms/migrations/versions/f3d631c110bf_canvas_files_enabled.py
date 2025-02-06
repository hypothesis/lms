"""
Make canvas files enabled an AI setting.

Revision ID: f3d631c110bf
Revises: 0b7391f5b1e3
Create Date: 2022-12-28 10:15:40.830444

"""

from alembic import op

revision = "f3d631c110bf"
down_revision = "5f0057d6d60f"


def upgrade():
    """
    Explicitly store the `files_enabled` setting for canvas instances.

    Currently the logic for this "setting" is:

    ```
    enabled = (request.product.family == Product.Family.CANVAS) and (
        "custom_canvas_course_id" in request.lti_params
        and application_instance.developer_key is not None
    )
    ```
    """
    conn = op.get_bind()
    result = conn.execute(
        """
        UPDATE application_instances
            SET settings = CASE
                WHEN settings = '{}' THEN '{"canvas": {"files_enabled": true}}'
                WHEN settings->'canvas' IS NULL THEN jsonb_set(settings, '{canvas}', '{"files_enabled": true}')
                ELSE jsonb_set(settings, '{canvas,files_enabled}', 'true')
            END
        WHERE
            developer_key IS NOT NULL
            AND (
                -- Check we have records for custom_canvas_course_id
                EXISTS (
                    SELECT id
                    FROM grouping
                    WHERE
                        type = 'course'
                        AND grouping.application_instance_id = application_instances.id
                        AND extra->'canvas'->>'custom_canvas_course_id' IS NOT NULL
                )
                -- Or has any other canvas feature enabled
                OR settings->'canvas'->>'sections_enabled' = 'true'
                OR settings->'canvas'->>'groups_enabled' = 'true'
            )
        """
    )
    print("\tApplication instances marked with canvas->files_enabled:", result.rowcount)  # noqa: T201


def downgrade():
    """No downgrade section as we might manually change some values after running `upgrade`."""
