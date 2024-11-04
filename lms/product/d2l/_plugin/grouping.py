from enum import Enum, StrEnum

from lms.models import Course, Grouping
from lms.product.plugin.grouping import GroupError, GroupingPlugin
from lms.services import D2LAPIClient, GroupSetService
from lms.services.exceptions import ExternalRequestError


class ErrorCodes(StrEnum):
    """Error codes that the FE is going to check for."""

    GROUP_SET_NOT_FOUND = "d2l_group_set_not_found"
    GROUP_SET_EMPTY = "d2l_group_set_empty"
    STUDENT_NOT_IN_GROUP = "d2l_student_not_in_group"


class D2LGroupingPlugin(GroupingPlugin):
    """A plugin which implements D2L specific grouping functions."""

    group_type = Grouping.Type.D2L_GROUP
    sections_type = None  # We don't support sections in D2L

    def __init__(
        self, d2l_api, api_user_id, misc_plugin, group_set_service: GroupSetService
    ):
        self._d2l_api = d2l_api
        self._api_user_id = api_user_id
        self._misc_plugin = misc_plugin
        self._group_set_service = group_set_service

    def get_group_sets(self, course: Course):
        group_sets = self._d2l_api.course_group_sets(course.lms_id)
        self._group_set_service.store_group_sets(course, group_sets)
        return group_sets

    def get_groups_for_learner(self, _svc, course, group_set_id):
        try:
            if learner_groups := self._d2l_api.group_set_groups(
                course.lms_id, group_set_id, self._api_user_id
            ):
                return learner_groups
        except ExternalRequestError as exc:
            if exc.status_code == 404:
                raise GroupError(
                    ErrorCodes.GROUP_SET_NOT_FOUND, group_set=group_set_id
                ) from exc

            raise

        raise GroupError(ErrorCodes.STUDENT_NOT_IN_GROUP, group_set=group_set_id)

    def get_groups_for_grading(
        self, svc, course, group_set_id, grading_student_id=None
    ):
        return svc.get_course_groupings_for_user(
            course,
            grading_student_id,
            type_=self.group_type,
            group_set_id=int(group_set_id),
        )

    def get_groups_for_instructor(self, _svc, course, group_set_id):
        try:
            groups = self._d2l_api.group_set_groups(course.lms_id, group_set_id)
        except ExternalRequestError as exc:
            if exc.status_code == 404:
                raise GroupError(
                    ErrorCodes.GROUP_SET_NOT_FOUND, group_set=group_set_id
                ) from exc

            raise

        if not groups:
            raise GroupError(ErrorCodes.GROUP_SET_EMPTY, group_set=group_set_id)

        return groups

    @classmethod
    def factory(cls, _context, request):
        d2l_api = request.find_service(D2LAPIClient)
        return cls(
            d2l_api=d2l_api,
            api_user_id=d2l_api.get_api_user_id(request.lti_user.user_id),
            misc_plugin=request.product.plugin.misc,
            group_set_service=request.find_service(GroupSetService),
        )
