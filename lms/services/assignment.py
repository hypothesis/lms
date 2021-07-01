from functools import lru_cache

from lms.models import Assignment


class AssignmentService:
    """A service for getting and setting assignments."""

    def __init__(self, db):
        self._db = db

    @lru_cache(maxsize=128)
    def get(self, tool_consumer_instance_guid, resource_link_id):
        return (
            self._db.query(Assignment)
            .filter_by(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                resource_link_id=resource_link_id,
            )
            .one_or_none()
        )

    def get_document_url(self, tool_consumer_instance_guid, resource_link_id):
        """
        Return the matching document URL or None.

        Return the document URL for the assignment with the given
        tool_consumer_instance_guid and resource_link_id, or None.
        """
        assignment = self.get(tool_consumer_instance_guid, resource_link_id)

        return assignment.document_url if assignment else None

    def set_document_url(
        self, tool_consumer_instance_guid, resource_link_id, document_url
    ):
        """
        Save the given document_url.

        Set the document_url for the assignment that matches
        tool_consumer_instance_guid and resource_link_id. Any existing document
        URL for this assignment will be overwritten.
        """
        assignment = self.get(tool_consumer_instance_guid, resource_link_id)

        if assignment:
            assignment.document_url = document_url
        else:
            self._db.add(
                Assignment(
                    document_url=document_url,
                    resource_link_id=resource_link_id,
                    tool_consumer_instance_guid=tool_consumer_instance_guid,
                )
            )

        # Clear the cache (@lru_cache) on self.get because we've changed the
        # contents of the DB. (Python's @lru_cache doesn't have a way to remove
        # just one key from the cache, you have to clear the entire cache.)
        self.get.cache_clear()


def factory(_context, request):
    return AssignmentService(db=request.db)
