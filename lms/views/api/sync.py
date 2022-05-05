from pyramid.view import view_config

from lms.security import Permissions
from lms.services import StudenGroupsService
from lms.validation import APIBlackboardSyncSchema


class Sync:
    def __init__(self, request):
        self.request = request
        self._students_groups_service = self.request.find_service(StudenGroupsService)

    @view_config(
        route_name="blackboard_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
        schema=APIBlackboardSyncSchema,
    )
    def blackboard_sync(self):
        groups = self._students_groups_service.get_groups(
            grading_user_id=self.request.parsed_params.get("gradingStudentId")
        )

        self._students_groups_service.sync_to_h(
            groups, self.request.parsed_params["group_info"]
        )
        authority = self.request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    @view_config(
        route_name="canvas_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
    )
    def canvas_sync(self):
        grading_user_id = None
        if self._is_speedgrader:
            grading_user_id = int(self.request.json["learner"]["canvas_user_id"])

        if self._is_canvas_group_launch:
            groups = self._students_groups_service.get_groups(
                grading_user_id=grading_user_id
            )
        else:
            groups = self._get_sections()

        self._students_groups_service.sync_to_h(groups)

        self._students_groups_service.sync_to_h(groups, self.request.json["group_info"])
        authority = self.request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    def sync_to_h(self, groups: List[Grouping], group_info: dict):
        self.request.find_service(name="lti_h").sync(groups, group_info)

    @property
    def _is_speedgrader(self):
        return "learner" in self._request.json

    @property
    def _is_canvas_group_launch(self):
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
