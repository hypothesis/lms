from typing import List

from lms.models import Grouping
from lms.services.exceptions import ExternalRequestError
from lms.services.product.grouping.interface import ProductGroupingService
from lms.views.api.exceptions import GroupError


class BlackboardGroupingService(ProductGroupingService):
    def __init__(self, user, lti_user, grouping_service, blackboard_api):
        super().__init__(user, lti_user, grouping_service)

        self._blackboard_api = blackboard_api

    def get_groups(self, course, group_set_id, grading_student_id) -> List[Grouping]:
        if self._lti_user.is_learner:
            learner_groups = self._blackboard_api.course_groups(
                course.lms_id, group_set_id, current_student_own_groups_only=True
            )
            if not learner_groups:
                raise BlackboardStudentNotInGroup(group_set=group_set_id)

            return learner_groups

        if grading_student_id:
            return self._grouping_service.get_course_groupings_for_user(
                course,
                grading_student_id,
                type_=Grouping.Type.BLACKBOARD_GROUP,
                group_set_id=group_set_id,
            )

        try:
            groups = self._blackboard_api.group_set_groups(course.lms_id, group_set_id)
        except ExternalRequestError as bb_api_error:
            if bb_api_error.status_code == 404:
                raise BlackboardGroupSetNotFound(
                    group_set=group_set_id
                ) from bb_api_error

            raise bb_api_error

        if not groups:
            raise BlackboardGroupSetEmpty(group_set=group_set_id)
        return self._to_groupings(Grouping.Type.BLACKBOARD_GROUP, groups, course)
