from pyramid.view import view_config

from lms.models import HGroup
from lms.security import Permissions
from lms.services import CanvasAPIClient, LTIHService


class Sync:
    def __init__(self, request):
        self._request = request

    @view_config(
        route_name="canvas_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
    )
    def sync(self):
        groups = self._to_groups(self._get_sections())

        self._sync_to_h(groups)

        authority = self._request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    @property
    def _is_speedgrader(self):
        return "learner" in self._request.json

    def _get_sections(self):
        canvas_api = self._request.find_service(CanvasAPIClient)
        course_id = self._request.json["course"]["custom_canvas_course_id"]
        lti_user = self._request.lti_user

        if lti_user.is_learner:
            # For learners we only want the client to show the sections that
            # the student belongs to, so fetch only the user's sections.
            return canvas_api.authenticated_users_sections(course_id)

        # For non-learners (e.g. instructors, teaching assistants) we want the
        # client to show all of the course's sections.
        sections = canvas_api.course_sections(course_id)
        if not self._is_speedgrader:
            return sections

        # SpeedGrader requests are made by the teacher, but we want the
        # learners sections. The canvas API won't give us names for those so
        # we will just use them to filter the course sections
        user_id = self._request.json["learner"]["canvas_user_id"]
        learner_section_ids = {
            sec["id"] for sec in canvas_api.users_sections(user_id, course_id)
        }

        return [sec for sec in sections if sec["id"] in learner_section_ids]

    def _to_groups(self, sections):
        tool_guid = self._request.json["lms"]["tool_consumer_instance_guid"]
        context_id = self._request.json["course"]["context_id"]

        return [
            HGroup.section_group(
                section_name=section["name"],
                tool_consumer_instance_guid=tool_guid,
                context_id=context_id,
                section_id=section["id"],
            )
            for section in sections
        ]

    def _sync_to_h(self, groups):
        lti_h_svc = self._request.find_service(LTIHService)
        group_info = self._request.json["group_info"]
        lti_h_svc.sync(groups, group_info)
