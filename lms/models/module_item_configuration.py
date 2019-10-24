import sqlalchemy as sa

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

    resource_link_id = sa.Column(sa.String, nullable=False)
    """The resource_link_id launch param of the module item or assignment."""

    tool_consumer_instance_guid = sa.Column(sa.String, nullable=False)
    """
    The tool_consumer_instance_guid launch param of the LMS.

    This is needed because resource_link_id's aren't guaranteed to be unique
    across different LMS's.
    """

    document_url = sa.Column(sa.String, nullable=False)
    """The URL of the document to be annotated for this assignment."""

    @classmethod
    def get_document_url(cls, db, tool_consumer_instance_guid, resource_link_id):
        """
        Return the matching document URL or None.

        Return the saved document URL for the given
        ``tool_consumer_instance_guid`` and ``resource_link_id``.

        Return ``None`` if there's no saved document URL.

        :rtype: str or None
        """
        mic = cls._get(db, tool_consumer_instance_guid, resource_link_id)

        if mic:
            return mic.document_url

        return None

    @classmethod
    def set_document_url(
        cls, db, tool_consumer_instance_guid, resource_link_id, document_url
    ):
        """
        Save the given ``document_url``.

        Set the document URL for the given ``tool_consumer_instance_guid`` and
        ``resource_link_id`` to ``document_url``.

        Any existing document URL for this ``tool_consumer_instance_guid`` and
        ``resource_link_id`` will be overwritten.
        """
        mic = cls._get(db, tool_consumer_instance_guid, resource_link_id)

        if mic:
            mic.document_url = document_url
        else:
            db.add(
                cls(
                    document_url=document_url,
                    resource_link_id=resource_link_id,
                    tool_consumer_instance_guid=tool_consumer_instance_guid,
                )
            )

    @classmethod
    def _get(cls, db, tool_consumer_instance_guid, resource_link_id):
        return (
            db.query(cls)
            .filter_by(
                resource_link_id=resource_link_id,
                tool_consumer_instance_guid=tool_consumer_instance_guid,
            )
            .one_or_none()
        )
