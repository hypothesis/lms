from pyramid.view import view_config

from lms.security import Permissions


class Sync:
    def __init__(self, request):
        self._request = request
        self._grouping_service = self._request.find_service(name="grouping")

    @view_config(
        route_name="canvas_api.sync",
        request_method="POST",
        renderer="json",
        permission=Permissions.API,
    )
    def sync(self):
        grading_user_id = self._request.json.get("learner", {}).get("canvas_user_id")
        if self._is_group_launch:
            groupings = self._grouping_service.get_groups(
                self._request.user,
                self._request.lti_user,
                self._get_course(),
                self.group_set(),
                grading_user_id,
            )

        else:
            groupings = self._grouping_service.get_sections(
                self._request.user,
                self._request.lti_user,
                self._get_course(),
                grading_user_id,
            )

        self._request.find_service(name="lti_h").sync(
            groupings, self._request.json["group_info"]
        )
        authority = self._request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groupings]

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

    def _get_course(self):
        return self._request.find_service(name="course").get_by_context_id(
            self._request.json["course"]["context_id"],
        )
