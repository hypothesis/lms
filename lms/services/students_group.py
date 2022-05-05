from lms.models import User, Grouping, LTIUser, User, ApplicationInstance
from typing import List
from lms.services import CanvasAPIError
from lms.services.exceptions import ExternalRequestError

from lms.views import (
    CanvasGroupSetEmpty,
    CanvasGroupSetNotFound,
    CanvasStudentNotInGroup,
)

from lms.views.api.exceptions import GroupError


class BlackboardStudentNotInGroup(GroupError):
    """Student doesn't belong to any of the groups in a group set assignment."""

    error_code = "blackboard_student_not_in_group"


class BlackboardGroupSetEmpty(GroupError):
    """Canvas GroupSet doesn't contain any groups."""

    error_code = "blackboard_group_set_empty"


class BlackboardGroupSetNotFound(GroupError):
    error_code = "blackboard_group_set_not_found"


class StudentGroupService:
    def __init__(self, grouping_service, course, group_set_id):
        self._grouping_service = grouping_service
        self._course = course
        self._group_set_id = group_set_id

    @property
    def grading(self) -> bool:
        return False

    def get_sections(self) -> List[Grouping]:
        raise NotImplementedError()

    def get_groups_for_current_user(self):
        raise NotImplementedError()

    def get_course_groups(self):
        raise NotImplementedError()

    def get_groups(
        self, lti_user: LTIUser, user: User, grading_user_id=None
    ) -> List[Grouping]:
        if lti_user.is_learner:
            # For learners, the groups they belong within the course
            api_groups = self.get_groups_for_current_user()
            groupings = self.to_groups_groupings(api_groups)
            self._grouping_service.upsert_grouping_memberships(user, groupings)

            return groupings

        if grading_user_id:
            # While grading requests are made by the teacher, get the student we are grading and its groups
            api_groups = self.get_groups_for_user_id(grading_user_id)
            groupings = self.to_groups_groupings(api_groups)
            return groupings

        # If not grading return all the groups in the course so the teacher can toggle between them.
        api_groups = self.get_course_groups()
        return self.to_groups_groupings(api_groups)

    def sync_to_h(self, groups: List[Grouping], group_info: dict):
        self.lti_h_service.sync(groups, group_info)

    def to_groups_groupings(self, api_groups: List[dict]):
        raise NotImplementedError()

    def _to_groups_groupings(self, groups, type_, group_set_dict_key):
        if groups and isinstance(groups[0], Grouping):
            return groups

        return self._grouping_service.upsert_with_parent(
            [
                {
                    "lms_id": group["id"],
                    "lms_name": group["name"],
                    "extra": {"group_set_id": group[group_set_dict_key]},
                }
                for group in groups
            ],
            parent=self._course,
            type_=type_,
        )


class BlackboardStudentsGroupsService(StudentGroupService):
    def __init__(self, grouping_service, course_id, group_set_id, blackboard_api):
        super().__init__(grouping_service, course_id, group_set_id)
        self._blackboard_api = blackboard_api

    def get_groups_for_current_user(self) -> List[dict]:
        api_groups = self._blackboard_api.course_groups(
            self._course.lms_id,
            self._group_set_id,
            current_student_own_groups_only=True,
        )
        if not api_groups:
            raise BlackboardStudentNotInGroup(group_set=self._group_set_id)

        return api_groups

    def get_groups_for_user_id(self, user_id: str) -> List[Grouping]:
        return self._grouping_service.get_course_groupings_for_user(
            self._course,
            user_id,
            type_=Grouping.Type.BLACKBOARD_GROUP,
            group_set_id=self._group_set_id,
        )

    def get_course_groups(self) -> List[dict]:
        try:
            api_groups = self._blackboard_api.group_set_groups(
                self._course.lms_id, self._group_set_id
            )
        except ExternalRequestError as bb_api_error:
            if bb_api_error.status_code == 404:
                raise BlackboardGroupSetNotFound(
                    group_set=self._group_set_id
                ) from bb_api_error

            raise bb_api_error

        if not api_groups:
            raise BlackboardGroupSetEmpty(group_set=self._group_set_id)

        return api_groups

    def to_groups_groupings(self, groups):
        return self._to_groups_groupings(
            groups, Grouping.Type.BLACKBOARD_GROUP, "groupSetId"
        )

    @staticmethod
    def group_set(request):
        return (
            request.find_service(name="assignment")
            .get(
                request.parsed_params["lms"]["tool_consumer_instance_guid"],
                request.parsed_params["assignment"]["resource_link_id"],
            )
            .extra["group_set_id"]
        )


class CanvasStudentsGroupsService(StudentGroupService):
    def __init__(self, grouping_service, course, group_set_id, canvas_api):
        super().__init__(grouping_service, course, group_set_id)
        self._canvas_api = canvas_api

    def to_groups_groupings(self, groups):
        return self._to_groups_groupings(
            groups, Grouping.Type.CANVAS_GROUP, "group_category_id"
        )

    def get_groups_for_current_user(self) -> List[dict]:
        api_groups = self._canvas_api.current_user_groups(
            self._canvas_course_id, self._group_set_id
        )
        if not api_groups:
            raise CanvasStudentNotInGroup(group_set=self._group_set_id)

        return api_groups

    def get_groups_for_user_id(self, user_id: str) -> List[dict]:
        return self._canvas_api.user_groups(
            self._canvas_course_id, int(user_id), self._group_set_id
        )

    def get_course_groups(self) -> List[dict]:
        try:
            groups = self._canvas_api.group_category_groups(self._group_set_id)
        except CanvasAPIError as canvas_api_error:
            raise CanvasGroupSetNotFound(
                group_set=self._group_set_id
            ) from canvas_api_error

        if not groups:
            raise CanvasGroupSetEmpty(group_set=self._group_set_id)

        return groups

    def get_sections(self, lti_user: LTIUser, user: User) -> List[Grouping]:
        if lti_user.is_learner:
            # For learners we only want the client to show the sections that
            # the student belongs to, so fetch only the user's sections.
            sections = self._to_section_groupings(
                self._canvas_api.authenticated_users_sections(self._canvas_course_id)
            )
            self._grouping_service.upsert_grouping_memberships(user, sections)
            return sections

        # For non-learners (e.g. instructors, teaching assistants) we want the
        # client to show all of the course's sections.
        sections = self._canvas_api.course_sections(self._canvas_course_id)
        if not self._is_speedgrader:
            return self._to_section_groupings(sections)

        # SpeedGrader requests are made by the teacher, but we want the
        # learners sections. The canvas API won't give us names for those so
        # we will just use them to filter the course sections
        user_id = self._request.json["learner"]["canvas_user_id"]
        learner_section_ids = {
            sec["id"]
            for sec in self._canvas_api.users_sections(user_id, self._canvas_course_id)
        }

        return self._to_section_groupings(
            [sec for sec in sections if sec["id"] in learner_section_ids]
        )

    @staticmethod
    def group_set(request):
        if self._is_speedgrader:
            return int(request.json["learner"].get("group_set"))

        return int(request.json["course"].get("group_set"))

    @property
    def _canvas_course_id(self):
        return self._course.extra["canvas"]["custom_canvas_course_id"]

    def _to_section_groupings(self, sections: List[dict]):
        return self._grouping_service.upsert_with_parent(
            [
                {
                    "lms_id": section["id"],
                    "lms_name": section["name"],
                }
                for section in sections
            ],
            parent=self._course,
            type_=Grouping.Type.CANVAS_SECTION,
        )


def factory(context, request):
    application_instance = request.find_service(
        name="application_instance"
    ).get_current()

    course_service = request.find_service(name="course")
    course = course_service.find_service(name="course").get(
        course_service.generate_authority_provided_id(
            request.json["lms"]["tool_consumer_instance_guid"],
            request.json["course"]["context_id"],
        )
    )

    if context.is_canvas:
        return CanvasStudentsGroupsService(
            request.find_service(name="grouping"),
            course,
            CanvasStudentsGroupsService.group_set(request),
            request.find_service(name="canvas_api_client"),
        )

    elif application_instance.product == ApplicationInstance.Product.BLACKBOARD:
        return CanvasStudentsGroupsService(
            request.find_service(name="grouping"),
            course,
            BlackboardStudentsGroupsService.group_set(request),
            request.find_service(name="canvas_api_client"),
        )

    else:
        raise NotImplementedError(
            "Students groups only implemented for Canvas and blackboard"
        )
