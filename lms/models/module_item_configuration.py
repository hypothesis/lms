import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

from lms.db import BASE

__all__ = ["ModuleItemConfiguration"]


class ModuleItemConfiguration(BASE):
    """
    A module item or assignment configuration.

    When an LMS doesn't support LTI content-item selection/deep linking (so it
    doesn't support storing an assignment's document URL in the LMS and passing
    it back to us in launch requests) then we store the document URL in the
    database instead.

    Each persisted ModuleItemConfiguration object represents a DB-stored
    assignment configuration, with the
    ``(tool_consumer_instance_guid, resource_link_id)`` launch params
    identifying the LTI resource (module item or assignment) and the
    ``document_url`` being the URL of the document to be annotated.
    """

    __tablename__ = "module_item_configurations"
    __table_args__ = (
        sa.UniqueConstraint("resource_link_id", "tool_consumer_instance_guid"),
    )

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    resource_link_id = sa.Column(sa.Unicode, nullable=False)
    """The resource_link_id launch param of the module item or assignment."""

    tool_consumer_instance_guid = sa.Column(sa.Unicode, nullable=False)
    """
    The tool_consumer_instance_guid launch param of the LMS.

    This is needed because resource_link_id's aren't guaranteed to be unique
    across different LMS's.
    """

    document_url = sa.Column(sa.Unicode, nullable=False)
    """The URL of the document to be annotated for this assignment."""

    extra = sa.Column(
        "extra",
        MutableDict.as_mutable(JSONB),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )

    def get_canvas_mapped_file_id(self, file_id):
        return self.extra.get("canvas_file_mappings", {}).get(file_id) or file_id

    def set_canvas_mapped_file_id(self, file_id, mapped_file_id):
        self.extra.setdefault("canvas_file_mappings", {})[file_id] = mapped_file_id
