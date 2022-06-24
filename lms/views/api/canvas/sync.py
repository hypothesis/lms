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
        course = self.get_course(self._request.json["course"]["context_id"])
        grading_user_id = self._request.json.get("learner", {}).get("canvas_user_id")

        if group_set_id := self._request.json["assignment"]["group_set_id"]:
            groupings = self._grouping_service.get_groups(
                self._request.user,
                self._request.lti_user,
                course,
                group_set_id,
                grading_user_id,
            )

        else:
            groupings = self._grouping_service.get_sections(
                self._request.user,
                self._request.lti_user,
                course,
                grading_user_id,
            )

        self._request.find_service(name="lti_h").sync(
            groupings, self._request.json["group_info"]
        )
        authority = self._request.registry.settings["h_authority"]
        return [group.groupid(authority) for group in groupings]

    def get_course(self, course_id):
        return self._request.find_service(name="course").get_by_context_id(course_id)
