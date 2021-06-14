from pyramid.view import view_config

from lms.security import Permissions


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
        if self.is_group_launch:
            groups = self._to_groups_groupings(self._get_canvas_groups())
        else:
            groups = self._to_section_groupings(self._get_sections())

        self._sync_to_h(groups)

        authority = self._request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    @property
    def _is_speedgrader(self):
        return "learner" in self._request.json

    @property
    def is_group_launch(self):
        return self._request.json["course"].get("group_set") is not None

    def _get_canvas_groups(self):
        lti_user = self._request.lti_user
        if lti_user.is_learner:
            groups = [self._canvas_learner_group()]
        else:
            groups = self._canvas_course_groups()

        return groups

    def _get_sections(self):
        course_id = self._request.json["course"]["custom_canvas_course_id"]
        lti_user = self._request.lti_user

        if lti_user.is_learner:
            # For learners we only want the client to show the sections that
            # the student belongs to, so fetch only the user's sections.
            return self._canvas_api.authenticated_users_sections(course_id)

        # For non-learners (e.g. instructors, teaching assistants) we want the
        # client to show all of the course's sections.
        sections = self._canvas_api.course_sections(course_id)
        if not self._is_speedgrader:
            return sections

        # SpeedGrader requests are made by the teacher, but we want the
        # learners sections. The canvas API won't give us names for those so
        # we will just use them to filter the course sections
        user_id = self._request.json["learner"]["canvas_user_id"]
        learner_section_ids = {
            sec["id"] for sec in self._canvas_api.users_sections(user_id, course_id)
        }

        return [sec for sec in sections if sec["id"] in learner_section_ids]

    def _to_groups_groupings(self, groups):
        tool_guid = self._request.json["lms"]["tool_consumer_instance_guid"]
        context_id = self._request.json["course"]["context_id"]

        return [
            self._grouping_service.canvas_group(
                tool_consumer_instance_guid=tool_guid,
                context_id=context_id,
                group_name=group["name"],
                group_id=group["id"],
                group_set_id=group["group_category_id"],
            )
            for group in groups
        ]

    def _to_section_groupings(self, sections):
        tool_guid = self._request.json["lms"]["tool_consumer_instance_guid"]
        context_id = self._request.json["course"]["context_id"]

        return [
            self._grouping_service.upsert_canvas_section(
                tool_consumer_instance_guid=tool_guid,
                context_id=context_id,
                section_id=section["id"],
                section_name=section["name"],
            )
            for section in sections
        ]

    def _sync_to_h(self, groups):
        lti_h_svc = self._request.find_service(name="lti_h")
        group_info = self._request.json["group_info"]
        lti_h_svc.sync(groups, group_info)

    def _canvas_learner_group(self):
        lti_user = self._request.lti_user
        if not lti_user.is_learner:
            return None

        group_set_id = int(self._request.json["course"]["group_set"])
        course_id = self._request.json["course"]["custom_canvas_course_id"]

        student_groups = self._canvas_api.course_groups(course_id, only_own_groups=True)

        course_group = [
            g for g in student_groups if g["group_category_id"] == group_set_id
        ]
        if not course_group:
            return None

        return course_group[0]

    def _canvas_course_groups(self):
        group_set_id = int(self._request.json["course"]["group_set"])

        return self._canvas_api.group_category_groups(group_set_id)
