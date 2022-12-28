"""
Make canvas files enabled an AI setting.

Revision ID: f3d631c110bf
Revises: 0b7391f5b1e3
Create Date: 2022-12-28 10:15:40.830444

"""
import sqlalchemy as sa
from alembic import op

revision = "f3d631c110bf"
down_revision = "0b7391f5b1e3"


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

    we can't access the first to conditions on the DB so we are only i8sing the last one.

    We'd only generate false positives so the worst case scenario is enabling
    this feature (the button in content selection) and not disabling it
    for any customers that are actively using it.
    """
    conn = op.get_bind()
    result = conn.execute(
        """UPDATE application_instances SET settings = settings || jsonb '{"canvas":{"files_enabled": true}}'
            WHERE developer_key is not null;"""
    )
    print("\tApplication instances marked with canvas->files_enabled:", result.rowcount)


def downgrade():
    """No downgrade section as we might manually change some values after running `upgrade`."""
    pass
