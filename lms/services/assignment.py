import logging
from functools import lru_cache

from lms.models import Assignment

log = logging.getLogger(__name__)


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
        """Get an assignment using using resource_link_id, ext_lti_assignment_id or both."""

        query = self._db.query(Assignment).filter(
            Assignment.tool_consumer_instance_guid == tool_consumer_instance_guid
        )
        if resource_link_id and not ext_lti_assignment_id:
            # Non canvas assignments
            query = query.filter(Assignment.resource_link_id == resource_link_id)
        elif not resource_link_id and ext_lti_assignment_id:
            # creating/editing a canvas assignment
            query = query.filter(
                Assignment.ext_lti_assignment_id == ext_lti_assignment_id
            )
        elif resource_link_id and ext_lti_assignment_id:
            query = query.filter(
                (
                    # Regular canvas launch
                    (
                        (Assignment.resource_link_id == resource_link_id)
                        & (Assignment.ext_lti_assignment_id == ext_lti_assignment_id)
                    )
                    # Configuring a file assignment that was stored in the DB
                    # before all canvas assignments were stored in the DB
                    | (
                        (Assignment.resource_link_id == resource_link_id)
                        & (Assignment.ext_lti_assignment_id.is_(None))
                    )
                    #  First launch of a newly configured assignment
                    | (
                        (Assignment.resource_link_id.is_(None))
                        & (Assignment.ext_lti_assignment_id == ext_lti_assignment_id)
                    )
                )
            )
        else:
            log.exception(
                "Can't get an assignment without neither resource_link_id or ext_lti_assignment_id"
            )
            return None

        assignments = query.all()
        if not assignments:
            return None

        if len(assignments) == 2:
            # We stored a canvas file assignment before (storing its resource_link_id)
            # we later configured it (storing its ext_lti_assignment_id) in a new row
            # and now we are launching it, we want to merge those two assignments
            old_assignment = (
                assignments[0] if assignments[0].resource_link_id else assignments[1]
            )
            assignment = (
                assignments[0]
                if assignments[0].ext_lti_assignment_id
                else assignments[1]
            )
            self._db.delete(old_assignment)
            self._db.flush()
        else:
            assignment = assignments[0]

        if resource_link_id and not assignment.resource_link_id:
            # First lunch of a canvas assignment, fill the resource_link_id now
            assignment.resource_link_id = resource_link_id

        return assignment

    def get_document_url(
        self,
        tool_consumer_instance_guid,
        resource_link_id=None,
        ext_lti_assignment_id=None,
    ):
        """
        Return the matching document URL or None.

        Return the document URL for the assignment with the given
        tool_consumer_instance_guid and resource_link_id, or None.
        """
        assignment = self.get(
            tool_consumer_instance_guid, resource_link_id, ext_lti_assignment_id
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
