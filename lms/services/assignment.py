import base64
import uuid
from functools import lru_cache

from lms.models import Assignment


class AssignmentService:
    """A service for getting and setting assignments."""

    def __init__(self, db):
        self._db = db

    @lru_cache(maxsize=128)
    def get(
        self,
        tool_consumer_instance_guid,
        resource_link_id=None,
        ext_lti_assignment_id=None,
    ):
        """
        Get an assignment using using either resource_link_id or ext_lti_assignment_id.

        When a canvas assignment has just been configured it will have
            resource_link_id=None and ext_lti_assignment_id!=None
        until it's first lunched.
        """
        assignment = (
            self._db.query(Assignment)
            .filter(
                Assignment.tool_consumer_instance_guid == tool_consumer_instance_guid,
                (
                    (Assignment.resource_link_id == resource_link_id)
                    | (Assignment.ext_lti_assignment_id == ext_lti_assignment_id)
                ),
            )
            .one_or_none()
        )

        if not assignment:
            return None

        if resource_link_id and not assignment.resource_link_id:
            # First lunch of the assignment, fill the resource_link_id now that we have it.
            assignment.resource_link_id = resource_link_id

        return assignment

    def get_document_url(
        self,
        tool_consumer_instance_guid,
        resource_link_id=None,
        hypothesis_assignment_id=None,
    ):
        """
        Return the matching document URL or None.

        Return the document URL for the assignment with the given
        tool_consumer_instance_guid and resource_link_id, or None.
        """
        assignment = self.get(
            tool_consumer_instance_guid, resource_link_id, hypothesis_assignment_id
        )
        return assignment.document_url if assignment else None

    def create(
        self,
        tool_consumer_instance_guid,
        document_url,
        resource_link_id=None,
        ext_lti_assignment_id=None,
    ):
        assignment = Assignment(
            tool_consumer_instance_guid=tool_consumer_instance_guid,
            document_url=document_url,
            resource_link_id=resource_link_id,
            ext_lti_assignment_id=ext_lti_assignment_id,
        )
        self._db.add(assignment)
        return assignment

    def set_document_url(
        self,
        tool_consumer_instance_guid,
        document_url,
        resource_link_id=None,
        ext_lti_assignment_id=None,
    ):
        """
        Save the given document_url in an existing assignment or create new one.

        Set the document_url for the assignment that matches
        tool_consumer_instance_guid and resource_link_id/ext_lti_assignment_id
        or create a new one if none exist on the DB.

        Any existing document URL for this assignment will be overwritten.
        """
        assignment = self.get(
            tool_consumer_instance_guid, resource_link_id, ext_lti_assignment_id
        )

        if assignment:
            assignment.document_url = document_url
        else:
            assignment = self.create(
                document_url=document_url,
                resource_link_id=resource_link_id,
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                ext_lti_assignment_id=ext_lti_assignment_id,
            )

        # Clear the cache (@lru_cache) on self.get because we've changed the
        # contents of the DB. (Python's @lru_cache doesn't have a way to remove
        # just one key from the cache, you have to clear the entire cache.)
        self.get.cache_clear()

        return assignment


def factory(_context, request):
    return AssignmentService(db=request.db)
