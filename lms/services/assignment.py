from functools import lru_cache

from lms.models import Assignment


class AssignmentService:
    """A service for getting and setting assignments."""

    def __init__(self, db):
        self._db = db

    def get_assignment(self, tool_consumer_instance_guid, resource_link_id):
        """Get an assignment by resource_link_id."""

        return (
            self._db.query(Assignment)
            .filter_by(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                resource_link_id=resource_link_id,
            )
            .one_or_none()
        )

    @lru_cache(maxsize=128)
    def assignment_exists(self, tool_consumer_instance_guid, resource_link_id) -> bool:
        return bool(self.get_assignment(tool_consumer_instance_guid, resource_link_id))

    def upsert_assignment(
        self, document_url, tool_consumer_instance_guid, resource_link_id, extra=None
    ):
        """
        Update or create an assignment with the given document_url.

        Set the document_url for the assignment that matches
        tool_consumer_instance_guid and resource_link_id
        or create a new one if none exist on the DB.

        Any existing document_url for this assignment will be overwritten.
        """
        assignment = self.get_assignment(tool_consumer_instance_guid, resource_link_id)
        if not assignment:
            assignment = Assignment(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                document_url=document_url,
                resource_link_id=resource_link_id,
            )
            self._db.add(assignment)

        assignment.document_url = document_url
        assignment.extra = extra if extra else assignment.extra or {}

        return assignment


def factory(_context, request):
    return AssignmentService(db=request.db)
