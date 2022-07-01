from enum import Enum

from lms.models import Grouping
from lms.product.plugin.grouping_service import GroupError, GroupingServicePlugin
from lms.services.exceptions import CanvasAPIError


class ErrorCodes(str, Enum):
    """Error codes that the FE is going to check for."""

    STUDENT_NOT_IN_GROUP = "canvas_student_not_in_group"
    GROUP_SET_EMPTY = "canvas_group_set_empty"
    GROUP_SET_NOT_FOUND = "canvas_group_set_not_found"


class CanvasGroupingPlugin(GroupingServicePlugin):
    """A plugin which implements Canvas specific grouping functions."""

    group_type = Grouping.Type.CANVAS_GROUP
    sections_type = Grouping.Type.CANVAS_SECTION

    def __init__(self, canvas_api):
        self._canvas_api = canvas_api

    def get_sections_for_learner(self, _svc, course):
        return self._canvas_api.authenticated_users_sections(
            self._custom_course_id(course)
        )

    def get_sections_for_instructor(self, _svc, course):
        return self._canvas_api.course_sections(self._custom_course_id(course))

    def get_sections_for_grading(self, _svc, course, grading_student_id):
        custom_course_id = self._custom_course_id(course)

        course_sections = self._canvas_api.course_sections(custom_course_id)

        # SpeedGrader requests are made by the teacher, but we want the
        # learners sections. The canvas API won't give us names for those so
        # we will just use them to filter the course sections
        learner_section_ids = {
            sec["id"]
            for sec in self._canvas_api.users_sections(
                grading_student_id, custom_course_id
            )
        }

        return [sec for sec in course_sections if sec["id"] in learner_section_ids]

    def get_groups_for_learner(self, _svc, course, group_set_id):
        # For learners, the groups they belong within the course
        if learner_groups := self._canvas_api.current_user_groups(
            self._custom_course_id(course), group_set_id
        ):
            return learner_groups

        raise GroupError(ErrorCodes.STUDENT_NOT_IN_GROUP, group_set=group_set_id)

    def get_groups_for_instructor(self, _svc, _course, group_set_id):
        try:
            # If not grading return all the groups in the course so the teacher can toggle between them.
            all_course_groups = self._canvas_api.group_category_groups(group_set_id)
        except CanvasAPIError as canvas_api_error:
            raise GroupError(
                ErrorCodes.GROUP_SET_NOT_FOUND, group_set=group_set_id
            ) from canvas_api_error

        if not all_course_groups:
            raise GroupError(ErrorCodes.GROUP_SET_EMPTY, group_set=group_set_id)

        return all_course_groups

    def get_groups_for_grading(
        self, _svc, course, group_set_id, grading_student_id=None
    ):
        # SpeedGrader requests are made by the teacher, get the student we are grading
        return self._canvas_api.user_groups(
            self._custom_course_id(course), grading_student_id, group_set_id
        )

    def _custom_course_id(self, course):
        return course.extra["canvas"]["custom_canvas_course_id"]

    @classmethod
    def factory(cls, _context, request):
        return cls(request.find_service(name="canvas_api_client"))
