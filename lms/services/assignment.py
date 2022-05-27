from functools import lru_cache
from typing import Optional

from lms.models import Assignment


class AssignmentService:
    """A service for getting and setting assignments."""

    def __init__(self, db):
        self._db = db

    @lru_cache(maxsize=128)
    def get(
        self,
        tool_consumer_instance_guid,
        resource_link_id,
    ) -> Optional[Assignment]:
        """Get an assignment using using resource_link_id."""
        return (
            self._db.query(Assignment)
            .filter_by(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                resource_link_id=resource_link_id,
            )
            .one_or_none()
        )

    @lru_cache(maxsize=128)
    def exists(
        self,
        tool_consumer_instance_guid,
        resource_link_id=None,
    ) -> bool:
        return bool(self.get(tool_consumer_instance_guid, resource_link_id))

    def upsert(
        self, document_url, tool_consumer_instance_guid, resource_link_id, extra=None
    ):
        """
        Update or create an assignment with the given document_url.

        Set the document_url for the assignment that matches
        tool_consumer_instance_guid and resource_link_id
        or create a new one if none exist on the DB.

        Any existing document_url for this assignment will be overwritten.
        """
        assignment = self.get(tool_consumer_instance_guid, resource_link_id)
        if not assignment:
            assignment = Assignment(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                document_url=document_url,
                resource_link_id=resource_link_id,
            )
            self._db.add(assignment)

        assignment.document_url = document_url
        if extra:
            assignment.extra = extra

        self._clear_cache()
        return assignment

    def _clear_cache(self):
        """
        Clear the cache (@lru_cache) because we've changed the contents of the DB.

        Python's @lru_cache doesn't have a way to remove
        just one key from the cache, you have to clear the entire cache.)
        """
        self.get.cache_clear()
        self.exists.cache_clear()


def factory(_context, request):
    return AssignmentService(db=request.db)
