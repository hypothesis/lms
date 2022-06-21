from lms.models import Grouping
from lms.services import CanvasAPIError
from lms.services.grouping._plugin.exceptions import GroupError
from lms.services.grouping.service import GroupingServicePlugin


class CanvasGroupingPlugin(GroupingServicePlugin):
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

        sections = self._canvas_api.course_sections(custom_course_id)

        # SpeedGrader requests are made by the teacher, but we want the
        # learners sections. The canvas API won't give us names for those so
        # we will just use them to filter the course sections
        learner_section_ids = {
            sec["id"]
            for sec in self._canvas_api.users_sections(
                grading_student_id, custom_course_id
            )
        }

        return [sec for sec in sections if sec["id"] in learner_section_ids]

    def get_groups_for_learner(self, _svc, course, group_set_id):
        # For learners, the groups they belong within the course
        if learner_groups := self._canvas_api.current_user_groups(
            self._custom_course_id(course), group_set_id
        ):
            return learner_groups

        raise GroupError(
            GroupError.ErrorCodes.CANVAS_STUDENT_NOT_IN_GROUP, group_set=group_set_id
        )

    def get_groups_for_instructor(self, _svc, _course, group_set_id):
        try:
            # If not grading return all the groups in the course so the teacher can toggle between them.
            all_course_groups = self._canvas_api.group_category_groups(group_set_id)
        except CanvasAPIError as canvas_api_error:
            raise GroupError(
                GroupError.ErrorCodes.CANVAS_GROUP_SET_NOT_FOUND, group_set=group_set_id
            ) from canvas_api_error

        if not all_course_groups:
            raise GroupError(
                GroupError.ErrorCodes.CANVAS_GROUP_SET_EMPTY, group_set=group_set_id
            )

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
