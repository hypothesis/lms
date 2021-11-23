"""Add a CHECK constraint to the grouping table."""
from alembic import op

revision = "4a4c2539c666"
down_revision = "f359b6f378a9"

constraint_name = "courses_must_NOT_have_parents_and_other_groupings_MUST_have_parents"
table_name = "grouping"


def upgrade():
    op.create_check_constraint(
        constraint_name,
        table_name=table_name,
        condition="(type='course' AND parent_id IS NULL) OR (type!='course' AND parent_id IS NOT NULL)",
    )


def downgrade():
    op.drop_constraint(constraint_name, table_name=table_name, type_="check")
