import sqlalchemy as sa
from lms.db import BASE


class ModuleItemConfiguration(BASE):
    """Class that links a document url to a specific lms module (Not needed for canvas)."""

    __tablename__ = "module_item_configurations"
    __table_args__ = (
        sa.UniqueConstraint("resource_link_id", "tool_consumer_instance_guid"),
    )

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    resource_link_id = sa.Column(sa.String, nullable=False)
    tool_consumer_instance_guid = sa.Column(sa.String, nullable=False)
    document_url = sa.Column(sa.String, nullable=False)
