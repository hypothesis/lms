from functools import lru_cache

from sqlalchemy.orm.exc import MultipleResultsFound

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
        """Get an assignment using using resource_link_id, ext_lti_assignment_id or both."""

        if not any([resource_link_id, ext_lti_assignment_id]):
            raise ValueError(
                "Can't get an assignment without neither resource_link_id or ext_lti_assignment_id"
            )

        if all([resource_link_id, ext_lti_assignment_id]):
            # When launching an assignment in Canvas there are both resource_link_id and
            # ext_lti_assignment_id launch params.
            assignments = self.get_for_canvas_launch(
                tool_consumer_instance_guid, resource_link_id, ext_lti_assignment_id
            )
            if len(assignments) > 1:
                raise MultipleResultsFound(
                    "Multiple assignments found. Should merge_canvas_assignments have been called"
                )
            return assignments[0] if assignments else None

        if ext_lti_assignment_id:
            # When creating or editing an assignment Canvas launches us with an
            # ext_lti_assignment_id but no resource_link_id.
            return self._get_for_canvas_assignment_config(
                tool_consumer_instance_guid, ext_lti_assignment_id
            )

        # Non-Canvas assignment launches always have a resource_link_id and never
        # have an ext_lti_assignment_id.
        return self._get_by_resource_link_id(
            tool_consumer_instance_guid, resource_link_id
        )

    @lru_cache(maxsize=128)
    def get_for_canvas_launch(
        self,
        tool_consumer_instance_guid,
        resource_link_id,
        ext_lti_assignment_id,
    ):
        """
        Return the assignment(s) with resource_link_id or ext_lti_assignment_id.

        Return all the assignments in the DB that have the given tool_consumer_instance_guid and
        either the given resource_link_id or ext_lti_assignment_id or both. This could be:

        1. A single assignment in the DB that has either the given resource_link_id or
           ext_lti_assignment_id or both

        2. Or two assignments:

           i.  One with the matching resource_link_id and no ext_lti_assignment_id
           ii. And one with the matching ext_lti_assignment_id and no resource_link_id

           The assignment with the resource_link_id will always be first in the sequence.

        :rtype: sequence of either 0, 1 or 2 models.Assignment objects
        """
        assert resource_link_id and ext_lti_assignment_id

        return (
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

    @lru_cache(maxsize=128)
    def exists(
        self,
        tool_consumer_instance_guid,
        resource_link_id=None,
        ext_lti_assignment_id=None,
    ) -> bool:
        try:
            return bool(
                self.get(
                    tool_consumer_instance_guid, resource_link_id, ext_lti_assignment_id
                )
            )
        except MultipleResultsFound:
            # Merge needed but it exists
            return True
        except ValueError:
            return False

    def set_document_url(  # pylint:disable=too-many-arguments
        self,
        document_url,
        tool_consumer_instance_guid,
        resource_link_id=None,
        ext_lti_assignment_id=None,
        extra=None,
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
        if not assignment:
            assignment = Assignment(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                document_url=document_url,
                resource_link_id=resource_link_id,
                ext_lti_assignment_id=ext_lti_assignment_id,
            )
            self._db.add(assignment)

        assignment.document_url = document_url
        assignment.extra = self._update_extra(assignment.extra, extra)

        self._clear_cache()
        return assignment

    @lru_cache(maxsize=128)
    def _get_by_resource_link_id(self, tool_consumer_instance_guid, resource_link_id):
        return (
            self._db.query(Assignment)
            .filter_by(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                resource_link_id=resource_link_id,
            )
            .one_or_none()
        )

    @lru_cache(maxsize=128)
    def _get_for_canvas_assignment_config(
        self, tool_consumer_instance_guid, ext_lti_assignment_id
    ):
        return (
            self._db.query(Assignment)
            .filter_by(
                tool_consumer_instance_guid=tool_consumer_instance_guid,
                ext_lti_assignment_id=ext_lti_assignment_id,
            )
            .one_or_none()
        )

    @staticmethod
    def _update_extra(old_extra, new_extra):
        new_extra = new_extra if new_extra else {}
        if not old_extra:
            return new_extra

        old_extra = dict(old_extra)
        if old_canvas_file_mappings := old_extra.get("canvas_file_mappings"):
            new_extra["canvas_file_mappings"] = old_canvas_file_mappings

        return new_extra

    def merge_canvas_assignments(self, old_assignment, new_assignment):
        """
        Merge two Canvas assignments into one and return the merged assignment.

        Merge old_assignment into new_assignment, delete old_assignment, and return the updated
        new_assignment.
        """
        new_extra = self._update_extra(old_assignment.extra, new_assignment.extra)

        self._db.delete(old_assignment)
        # Flushing early so the `resource_link_id` constraints doesn't
        # conflict between the deleted record and new_assignment .
        self._db.flush()

        new_assignment.extra = new_extra
        new_assignment.resource_link_id = old_assignment.resource_link_id

        self._clear_cache()
        return new_assignment

    def _clear_cache(self):
        """
        Clear the cache (@lru_cache) because we've changed the contents of the DB.

        Python's @lru_cache doesn't have a way to remove
        just one key from the cache, you have to clear the entire cache.)
        """
        self.get.cache_clear()
        # Private methods are cached so different but equivalent args to get
        # (default values, args vs kwargs) still don't hit the database.
        self._get_by_resource_link_id.cache_clear()
        self._get_for_canvas_assignment_config.cache_clear()
        self.get_for_canvas_launch.cache_clear()
        self.exists.cache_clear()


def factory(_context, request):
    return AssignmentService(db=request.db)
