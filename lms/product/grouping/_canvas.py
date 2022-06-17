from typing import List

from lms.models import Grouping
from lms.product.grouping.interface import GroupingPlugin
from lms.services import CanvasAPIError


class CanvasGroupingPlugin(GroupingPlugin):
    def __init__(self, user, lti_user, canvas_api_client):
        super().__init__(user, lti_user)
        self._canvas_api = canvas_api_client

    def get_sections(
        self, grouping_service, course, grading_student_id=None
    ) -> List[Grouping]:
        custom_course_id = course.extra["canvas"]["custom_canvas_course_id"]

        if self._lti_user.is_learner:
            # For learners we only want the client to show the sections that
            # the student belongs to, so fetch only the user's sections.
            student_sections = self._canvas_api.authenticated_users_sections(
                custom_course_id
            )
            return self._to_groupings(
                Grouping.Type.CANVAS_SECTION, student_sections, course
            )

        # For non-learners (e.g. instructors, teaching assistants) we want the
        # client to show all of the course's sections.
        sections = self._canvas_api.course_sections(custom_course_id)
        if not grading_student_id:
            return self._to_groupings(Grouping.Type.CANVAS_SECTION, sections, course)

        # SpeedGrader requests are made by the teacher, but we want the
        # learners sections. The canvas API won't give us names for those so
        # we will just use them to filter the course sections
        learner_section_ids = {
            sec["id"]
            for sec in self._canvas_api.users_sections(
                grading_student_id, custom_course_id
            )
        }

        return self._to_groupings(
            Grouping.Type.CANVAS_SECTION,
            [sec for sec in sections if sec.lms_id in learner_section_ids],
            course,
        )

    def get_groups(self, course, group_set_id, grading_student_id) -> List[Grouping]:
        custom_course_id = course.extra["canvas"]["custom_canvas_course_id"]

        if self._lti_user.is_learner:
            # For learners, the groups they belong within the course
            learner_groups = self._canvas_api.current_user_groups(
                custom_course_id, group_set_id
            )
            if not learner_groups:
                raise CanvasStudentNotInGroup(group_set=group_set_id)

            return self._to_groupings(
                Grouping.Type.CANVAS_GROUP, learner_groups, course
            )

        if grading_student_id:
            # SpeedGrader requests are made by the teacher, get the student we are grading
            graded_student_groups = self._canvas_api.user_groups(
                custom_course_id, grading_student_id, group_set_id
            )
            return self._to_groupings(
                Grouping.Type.CANVAS_GROUP, graded_student_groups, course
            )

        try:
            # If not grading return all the groups in the course so the teacher can toggle between them.
            all_course_groups = self._canvas_api.group_category_groups(group_set_id)
        except CanvasAPIError as canvas_api_error:
            raise CanvasGroupSetNotFound(group_set=group_set_id) from canvas_api_error

        if not all_course_groups:
            raise CanvasGroupSetEmpty(group_set=group_set_id)

        return self._to_groupings(Grouping.Type.CANVAS_GROUP, all_course_groups, course)
