from typing import List

from pyramid.view import view_config

from lms.models import Grouping
from lms.security import Permissions
from lms.services import CanvasAPIError, UserService
from lms.views import (
    CanvasGroupSetEmpty,
    CanvasGroupSetNotFound,
    CanvasStudentNotInGroup,
)


class Sync:
    def __init__(self, request):
        self._request = request
        self._grouping_service = self._request.find_service(name="grouping")
        self._canvas_api = self._request.find_service(name="canvas_api_client")

    @view_config(
        route_name="canvas_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
    )
    def sync(self):
        if self._is_group_launch:
            groups = self._get_canvas_groups()
        else:
            groups = self._get_sections()

        self._sync_to_h(groups)

        authority = self._request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    @property
    def _is_speedgrader(self):
        return "learner" in self._request.json

    def group_set(self):
        if self._is_speedgrader:
            return int(self._request.json["learner"].get("group_set"))

        return int(self._request.json["course"].get("group_set"))

    @property
    def _is_group_launch(self):
        application_instance = self._request.find_service(
            name="application_instance"
        ).get_current()
        if not application_instance.settings.get("canvas", "groups_enabled"):
            return False

        try:
            self.group_set()
        except (KeyError, ValueError, TypeError):
            return False
        else:
            return True

    def _get_canvas_groups(self):
        lti_user = self._request.lti_user
        group_set_id = self.group_set()
        if lti_user.is_learner:
            user = self._get_user(lti_user.user_id)

            # For learners, the groups they belong within the course
            learner_groups = self._canvas_api.current_user_groups(
                self._request.json["course"]["custom_canvas_course_id"],
                group_set_id,
            )
            if not learner_groups:
                raise CanvasStudentNotInGroup(group_set=group_set_id)

            groups = self._to_groups_groupings(learner_groups)
            self._grouping_service.upsert_grouping_memberships(user, groups)

            return groups

        if self._is_speedgrader:
            # SpeedGrader requests are made by the teacher, get the student we are grading
            return self._to_groups_groupings(
                self._canvas_api.user_groups(
                    self._request.json["course"]["custom_canvas_course_id"],
                    int(self._request.json["learner"]["canvas_user_id"]),
                    self.group_set(),
                )
            )

        try:
            # If not grading return all the groups in the course so the teacher can toggle between them.
            groups = self._canvas_api.group_category_groups(group_set_id)
        except CanvasAPIError as canvas_api_error:
            raise CanvasGroupSetNotFound(group_set=group_set_id) from canvas_api_error

        if not groups:
            raise CanvasGroupSetEmpty(group_set=group_set_id)

        return self._to_groups_groupings(groups)

    def _get_sections(self) -> List[Grouping]:
        course_id = self._request.json["course"]["custom_canvas_course_id"]
        lti_user = self._request.lti_user

        if lti_user.is_learner:
            user = self._get_user(lti_user.user_id)

            # For learners we only want the client to show the sections that
            # the student belongs to, so fetch only the user's sections.
            sections = self._to_section_groupings(
                self._canvas_api.authenticated_users_sections(course_id)
            )
            self._grouping_service.upsert_grouping_memberships(user, sections)
            return sections

        # For non-learners (e.g. instructors, teaching assistants) we want the
        # client to show all of the course's sections.
        sections = self._canvas_api.course_sections(course_id)
        if not self._is_speedgrader:
            return self._to_section_groupings(sections)

        # SpeedGrader requests are made by the teacher, but we want the
        # learners sections. The canvas API won't give us names for those so
        # we will just use them to filter the course sections
        user_id = self._request.json["learner"]["canvas_user_id"]
        learner_section_ids = {
            sec["id"] for sec in self._canvas_api.users_sections(user_id, course_id)
        }

        return self._to_section_groupings(
            [sec for sec in sections if sec["id"] in learner_section_ids]
        )

    def _to_groups_groupings(self, groups):
        course = self._get_course()

        return self._grouping_service.upsert_with_parent(
            [
                {
                    "lms_id": group["id"],
                    "lms_name": group["name"],
                    "extra": {"group_set_id": group["group_category_id"]},
                }
                for group in groups
            ],
            parent=course,
            type_=Grouping.Type.CANVAS_GROUP,
        )

    def _to_section_groupings(self, sections):
        course = self._get_course()

        return self._grouping_service.upsert_with_parent(
            [
                {
                    "lms_id": section["id"],
                    "lms_name": section["name"],
                }
                for section in sections
            ],
            parent=course,
            type_=Grouping.Type.CANVAS_SECTION,
        )

    def _get_course(self):
        return self._request.find_service(name="course").get(
            self._request.json["lms"]["tool_consumer_instance_guid"],
            self._request.json["course"]["context_id"],
        )

    def _get_user(self, user_id):
        return self._request.find_service(UserService).get(
            self._request.find_service(name="application_instance").get_current(),
            user_id,
        )

    def _sync_to_h(self, groups):
        lti_h_svc = self._request.find_service(name="lti_h")
        group_info = self._request.json["group_info"]
        lti_h_svc.sync(groups, group_info)
