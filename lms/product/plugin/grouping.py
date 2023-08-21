from enum import Enum

from lms.models import Course, Grouping


# pylint: disable=unused-argument
class GroupingPlugin:
    """
    An abstraction between a specific LMS API and different grouping types.

    This is intended to give a place for product specific actions to take
    place. For example if you are creating a Canvas plugin, it will be implicit
    that you are always in a Canvas context.

    All methods currently return a list of groupings, or dicts of values to
    create groupings from, or `None` if the particular function is not
    supported in this LMS.
    """

    group_type: Grouping.Type | None = None
    """The type of groups this plugin supports. `None` disables support."""

    sections_type: Grouping.Type | None = None
    """The type of sections this plugin supports. `None` disables support."""

    def get_sections_for_learner(
        self, svc, course: Course
    ) -> list | None:  # pragma: nocover
        """Get the sections from context when launched by a normal learner."""

        return None

    def get_sections_for_instructor(
        self, svc, course: Course
    ) -> list | None:  # pragma: nocover
        """Get the sections from context when launched by an instructor."""

        return None

    def get_sections_for_grading(
        self, svc, course: Course, grading_student_id
    ) -> list | None:  # pragma: nocover
        """Get the sections for a learner when they are being graded."""

        return None

    def get_group_sets(self, course) -> list[dict]:  # pragma: nocover
        """Return the list of group sets for the given course."""
        return []

    def get_groups_for_learner(
        self, svc, course: Course, group_set_id
    ) -> list | None:  # pragma: nocover
        """Get the sections from context when launched by a normal learner."""

        return None

    def get_groups_for_instructor(
        self, svc, course: Course, group_set_id
    ) -> list | None:  # pragma: nocover
        """Get the groups from context when launched by an instructor."""

        return None

    def get_groups_for_grading(
        self, svc, course: Course, group_set_id, grading_student_id
    ) -> list | None:  # pragma: nocover
        """Get the groups for a learner when they are being graded."""

        return None

    def sections_enabled(self, request, application_instance, course) -> bool:
        """Check if sections are enabled for this LMS, instance and course."""
        return bool(self.sections_type)

    def get_group_set_id(self, _request, assignment, historical_assignment=None):
        """
        Get the group set ID for group launches.

        A course can be divided in multiple "small groups" but it's possible to
        have different sets of groups for the same course.

        This ID identifies a collection of groups.

        `historical_assignment` might be none even when it might exist on the DB
        (or even available as assignment.copied_form). The historical_assignment
        is only relevant to get the config when creating an assignment for the
        first time.
        """
        if not self.group_type:
            # Groups not enabled on this product
            return None

        if assignment:
            return assignment.extra.get("group_set_id")

        if historical_assignment:
            # When creating new assignments, take the value from the previous
            # version of the assignment
            return historical_assignment.extra.get("group_set_id")

        return None


class GroupError(Exception):
    """Exceptions raised by plugins."""

    def __init__(self, error_code: Enum, group_set):
        self.error_code = error_code
        self.details = {"group_set": group_set}
        super().__init__(self.details)
