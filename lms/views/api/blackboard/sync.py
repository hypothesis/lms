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
        groups = self._students_groups_service.get_groups()

        self._students_groups_service.sync_to_h(groups)
        authority = self.request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    @view_config(
        route_name="canvas_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
    )
    def canvas_sync(self):
        if self._is_canvas_group_launch:
            groups = self._students_groups_service.get_groups()
        else:
            groups = self._students_groups_service._get_sections()

        self._students_groups_service.sync_to_h(groups)

        authority = self.request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groups]

    @property
    def _is_canvas_group_launch(self):
        application_instance = self.request.find_service(
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
