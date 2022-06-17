from lms.models import Grouping
from lms.services import ExternalRequestError
from lms.services.grouping.service import GroupingServicePlugin
from lms.views.api.exceptions import GroupError


class BlackboardStudentNotInGroup(GroupError):
    """Student doesn't belong to any of the groups in a group set assignment."""

    error_code = "blackboard_student_not_in_group"


class BlackboardGroupSetEmpty(GroupError):
    """Canvas GroupSet doesn't contain any groups."""

    error_code = "blackboard_group_set_empty"


class BlackboardGroupSetNotFound(GroupError):
    error_code = "blackboard_group_set_not_found"


class BlackboardGroupingPlugin(GroupingServicePlugin):
    group_type = Grouping.Type.BLACKBOARD_GROUP
    sections_type = None

    def __init__(self, blackboard_api):
        self._blackboard_api = blackboard_api

    def get_groups_for_learner(self, svc, course, group_set_id):
        if learner_groups := self._blackboard_api.course_groups(
            course.lms_id, group_set_id, current_student_own_groups_only=True
        ):
            return learner_groups

        raise BlackboardStudentNotInGroup(group_set=group_set_id)

    def get_groups_for_grading(
        self, svc, course, group_set_id, grading_student_id=None
    ):
        return svc.get_course_groupings_for_user(
            course, grading_student_id, type_=self.group_type, group_set_id=group_set_id
        )

    def get_groups_for_instructor(self, svc, course, group_set_id):
        try:
            groups = self._blackboard_api.group_set_groups(course.lms_id, group_set_id)
        except ExternalRequestError as exc:
            if exc.status_code == 404:
                raise BlackboardGroupSetNotFound(group_set=group_set_id) from exc

            raise

        if not groups:
            raise BlackboardGroupSetEmpty(group_set=group_set_id)

        return groups
