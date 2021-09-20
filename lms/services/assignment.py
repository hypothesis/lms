import logging
from functools import lru_cache

from sqlalchemy.orm.exc import NoResultFound

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

        if not any([resource_link_id, ext_lti_assignment_id]):
            raise ValueError(
                "Can't get an assignment without neither resource_link_id or ext_lti_assignment_id"
            )

        # Non canvas assignments, just use `resource_link_id`
        if resource_link_id and not ext_lti_assignment_id:
            return self._get_by_resource_link_id(
                tool_consumer_instance_guid, resource_link_id
            )

        # Creating/editing a canvas assignment, only `ext_lti_assignment_id` is available
        if not resource_link_id and ext_lti_assignment_id:
            return self._get_by_ext_lti_assignment(
                tool_consumer_instance_guid, ext_lti_assignment_id
            )

        # We have both ext_lti_assignment_id and resource_link_id, canvas launch.
        return self._get_for_canvas_launch(
            tool_consumer_instance_guid, resource_link_id, ext_lti_assignment_id
        )

    def exists(
        self,
        tool_consumer_instance_guid,
        resource_link_id=None,
        ext_lti_assignment_id=None,
    ) -> bool:
        try:
            self.get(
                tool_consumer_instance_guid, resource_link_id, ext_lti_assignment_id
            )
        except (NoResultFound, ValueError):
            return False
        else:
            return True

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
        try:
            assignment = self.get(
                tool_consumer_instance_guid, resource_link_id, ext_lti_assignment_id
            )
            assignment.document_url = document_url
        except NoResultFound:
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

    def _merge_canvas_assignments(self, assignments):
        # We stored a canvas file assignment before (storing its resource_link_id)
        # we later configured it (storing its ext_lti_assignment_id) in a new row
        # and now we are launching it, we want to merge those two assignments

        # order is guaranteed by the query's `order by`
        old_assignment, new_assignment = assignments

        assert not old_assignment.ext_lti_assignment_id
        assert not new_assignment.resource_link_id

        self._db.delete(old_assignment)
        # Flushing early so the `resource_link_id` constraints doesn't
        # conflict between the deleted record and new_assignment .
        self._db.flush()

        new_assignment.resource_link_id = old_assignment.resource_link_id
        return new_assignment

    def _get_by_resource_link_id(self, tool_consumer_instance_guid, resource_link_id):
        return (
            self._db.query(Assignment)
            .filter_by(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                resource_link_id=resource_link_id,
            )
            .one()
        )

    def _get_by_ext_lti_assignment(
        self, tool_consumer_instance_guid, ext_lti_assignment_id
    ):
        return (
            self._db.query(Assignment)
            .filter_by(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                ext_lti_assignment_id=ext_lti_assignment_id,
            )
            .one()
        )

    def _get_for_canvas_launch(
        self,
        tool_consumer_instance_guid,
        resource_link_id,
        ext_lti_assignment_id,
    ):
        """Get a canvas assignment by both resource_link_id and ext_lti_assignment_id."""
        assignments = (
            self._db.query(Assignment)
            .filter(
                Assignment.tool_consumer_instance_guid == tool_consumer_instance_guid,
                (
                    (
                        (Assignment.resource_link_id == resource_link_id)
                        & (Assignment.ext_lti_assignment_id == ext_lti_assignment_id)
                    )
                    | (
                        (Assignment.resource_link_id == resource_link_id)
                        & (Assignment.ext_lti_assignment_id.is_(None))
                    )
                    | (
                        (Assignment.resource_link_id.is_(None))
                        & (Assignment.ext_lti_assignment_id == ext_lti_assignment_id)
                    )
                ),
            )
            .order_by(Assignment.resource_link_id.asc())
            .all()
        )

        if not assignments:
            raise NoResultFound()

        if len(assignments) == 2:
            # We found two assignments: one with the matching resource_link_id and no ext_lti_assignment_id
            # and one with the matching ext_lti_assignment_id and no resource_link_id.
            #
            # This happens because legacy code used to store Canvas assignments in the DB with a
            # resource_link_id and no ext_lti_assignment_id, see https://github.com/hypothesis/lms/pull/2780
            #
            # Whereas current code stores Canvas assignments during content-item-selection with an
            # ext_lti_assignment_id and no resource_link_id.
            #
            # We need to merge the two assignments into one.
            assignment = self._merge_canvas_assignments(assignments)
        else:
            assignment = assignments[0]

        if resource_link_id and not assignment.resource_link_id:
            # We found an assignment with an ext_lti_assignment_id but no resource_link_id.
            # This happens the first time a new Canvas assignment is launched: the assignment got created
            # during content-item-selection with an ext_lti_assignment_id but no resource_link_id,
            # and then the first time the assignment is launched we add the resource_link_id.
            assignment.resource_link_id = resource_link_id

        # We found an assignment with the matching resource_link_id and ext_lti_assignment_id.kk
        return assignment


def factory(_context, request):
    return AssignmentService(db=request.db)
