from enum import Enum
from typing import List, Optional

from lms.models import Course, Grouping


# pylint: disable=unused-argument
class GroupingServicePlugin:  # pragma: no cover
    """
    An interface between the grouping service and a specific LMS.

    This is intended to give a place for product specific actions to take
    place. For example if you are creating a Canvas plugin, it will be implicit
    that you are always in a Canvas context.

    All methods currently return a list of groupings, or dicts of values to
    create groupings from, or `None` if the particular function is not
    supported in this LMS.
    """

    group_type: Grouping.Type = None
    """The type of groups this plugin supports. `None` disables support."""

    sections_type: Grouping.Type = None
    """The type of sections this plugin supports. `None` disables support."""

    def get_sections_for_learner(self, svc, course) -> Optional[List]:
        """Get the sections from context when launched by a normal learner."""

        return None

    def get_sections_for_instructor(self, svc, course: Course) -> Optional[List]:
        """Get the sections from context when launched by an instructor."""

        return None

    def get_sections_for_grading(
        self, svc, course: Course, grading_student_id
    ) -> Optional[List]:
        """Get the sections for a learner when they are being graded."""

        return None

    def get_groups_for_learner(
        self, svc, course: Course, group_set_id
    ) -> Optional[List]:
        """Get the sections from context when launched by a normal learner."""

        return None

    def get_groups_for_instructor(
        self, svc, course: Course, group_set_id
    ) -> Optional[List]:
        """Get the groups from context when launched by an instructor."""

        return None

    def get_groups_for_grading(
        self, svc, course: Course, group_set_id, grading_student_id
    ) -> Optional[List]:
        """Get the groups for a learner when they are being graded."""

        return None


class GroupError(Exception):
    """Exceptions raised by plugins."""

    class ErrorCodes(str, Enum):
        """Error codes that the FE is going to check for."""

        CANVAS_STUDENT_NOT_IN_GROUP = "canvas_student_not_in_group"
        CANVAS_GROUP_SET_EMPTY = "canvas_group_set_empty"
        CANVAS_GROUP_SET_NOT_FOUND = "canvas_group_set_not_found"
        BLACKBOARD_GROUP_SET_NOT_FOUND = "blackboard_group_set_not_found"
        BLACKBOARD_GROUP_SET_EMPTY = "blackboard_group_set_empty"
        BLACKBOARD_STUDENT_NOT_IN_GROUP = "blackboard_student_not_in_group"

    def __init__(self, error_code, group_set):
        self.error_code = error_code
        self.details = {"group_set": group_set}
        super().__init__(self.details)
