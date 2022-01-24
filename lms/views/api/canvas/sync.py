from pyramid.view import view_config

from lms.models import Grouping
from lms.security import Permissions
from lms.services import CanvasAPIError, CanvasService, UserService
from lms.views import (
    CanvasGroupSetEmpty,
    CanvasGroupSetNotFound,
    CanvasStudentNotInGroup,
)


class Sync:
    def __init__(self, request):
        self._request = request
        self._grouping_service = self._request.find_service(name="grouping")
        self._canvas: CanvasService = self._request.find_service(iface=CanvasService)
        self._course_service = self._request.find_service(name="course")

    @view_config(
        route_name="canvas_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
    )
    def sync(self):
        if self._canvas.is_group_launch(self._request):
            groups = self._get_canvas_groups()
        else:
            groups = self._to_section_groupings(self._get_sections())

        self._sync_to_h(groups)

        authority = self._request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    def _get_canvas_groups(self):
        lti_user = self._request.lti_user
        group_set_id = self._canvas.group_set(self._request)
        if lti_user.is_learner:
            user = self._request.find_service(UserService).get(
                self._request.find_service(name="application_instance").get_current(),
                lti_user.user_id,
            )

            # For learners, the groups they belong within the course
            learner_groups = self._canvas.api.current_user_groups(
                self._request.json["course"]["custom_canvas_course_id"],
                group_set_id,
            )
            if not learner_groups:
                raise CanvasStudentNotInGroup(group_set=group_set_id)

            groups = self._to_groups_groupings(learner_groups)
            self._grouping_service.upsert_grouping_memberships(user, groups)

            return groups

        if self._canvas.is_speedgrader(self._request):
            # SpeedGrader requests are made by the teacher, get the student we are grading
            return self._to_groups_groupings(
                self._canvas.api.user_groups(
                    self._request.json["course"]["custom_canvas_course_id"],
                    int(self._request.json["learner"]["canvas_user_id"]),
                    group_set_id,
                )
            )

        try:
            # If not grading return all the groups in the course so the teacher can toggle between them.
            groups = self._canvas.api.group_category_groups(group_set_id)
        except CanvasAPIError as canvas_api_error:
            raise CanvasGroupSetNotFound(group_set=group_set_id) from canvas_api_error

        if not groups:
            raise CanvasGroupSetEmpty(group_set=group_set_id)

        return self._to_groups_groupings(groups)

    def _get_sections(self):
        course_id = self._request.json["course"]["custom_canvas_course_id"]
        lti_user = self._request.lti_user

        if lti_user.is_learner:
            # For learners we only want the client to show the sections that
            # the student belongs to, so fetch only the user's sections.
            return self._canvas.api.authenticated_users_sections(course_id)

        # For non-learners (e.g. instructors, teaching assistants) we want the
        # client to show all of the course's sections.
        sections = self._canvas.api.course_sections(course_id)
        if not CanvasService.is_speedgrader(self._request):
            return sections

        # SpeedGrader requests are made by the teacher, but we want the
        # learners sections. The canvas API won't give us names for those so
        # we will just use them to filter the course sections
        user_id = self._request.json["learner"]["canvas_user_id"]
        learner_section_ids = {
            sec["id"] for sec in self._canvas.api.users_sections(user_id, course_id)
        }

        return [sec for sec in sections if sec["id"] in learner_section_ids]

    def _to_groups_groupings(self, groups):
        tool_guid = self._request.json["lms"]["tool_consumer_instance_guid"]
        course = self._get_course()

        return [
            self._grouping_service.upsert_with_parent(
                tool_consumer_instance_guid=tool_guid,
                lms_id=group["id"],
                lms_name=group["name"],
                parent=course,
                type_=Grouping.Type.CANVAS_GROUP,
                extra={"group_set_id": group["group_category_id"]},
            )
            for group in groups
        ]

    def _to_section_groupings(self, sections):
        tool_guid = self._request.json["lms"]["tool_consumer_instance_guid"]
        course = self._get_course()

        return [
            self._grouping_service.upsert_with_parent(
                tool_consumer_instance_guid=tool_guid,
                lms_id=section["id"],
                lms_name=section["name"],
                parent=course,
                type_=Grouping.Type.CANVAS_SECTION,
            )
            for section in sections
        ]

    def _get_course(self):
        tool_guid = self._request.json["lms"]["tool_consumer_instance_guid"]
        context_id = self._request.json["course"]["context_id"]

        return self._course_service.get(
            self._course_service.generate_authority_provided_id(tool_guid, context_id)
        )

    def _sync_to_h(self, groups):
        lti_h_svc = self._request.find_service(name="lti_h")
        group_info = self._request.json["group_info"]
        lti_h_svc.sync(groups, group_info)
