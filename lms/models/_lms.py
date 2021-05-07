import sqlalchemy as sa

from lms.db import BASE


class LMS(BASE):
    __tablename__ = "lms"
    __table_args__ = (
        sa.UniqueConstraint("application_instance_id", "tool_consumer_instance_guid"),
    )

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    application_instance_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
    )

    tool_consumer_instance_guid = sa.Column(sa.String, nullable=False)

    tool_consumer_info_product_family_code = sa.Column(sa.UnicodeText(), nullable=True)
