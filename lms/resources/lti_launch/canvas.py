from lms.resources.lti_launch.base import LTILaunchResource
from lms.services import ApplicationInstanceNotFound


class CanvasLTILaunchResource(LTILaunchResource):
    @property
    def is_canvas(self) -> bool:
        return True

    @property
    def is_group_launch(self):
        """Return True if the current assignment uses canvas groups."""
        try:
            int(self._request.params["group_set"])
        except (KeyError, ValueError, TypeError):
            return False
        else:
            return True

    def groups_enabled(self):
        """Return True if Canvas groups are enabled at the school/installation level."""
        try:
            application_instance = self._application_instance_service.get_current()
        except ApplicationInstanceNotFound:
            return False

        return bool(application_instance.settings.get("canvas", "groups_enabled"))

    @property
    def _is_speedgrader(self):
        return bool(self._request.GET.get("learner_canvas_user_id"))

    @property
    def is_legacy_speedgrader(self):
        """
        Return True if the current request is a legacy SpeedGrader launch.

        To work around a Canvas bug we add the assignment's resource_link_id as
        a query param on the LTI launch URLs that we submit to SpeedGrader (see
        https://github.com/instructure/canvas-lms/issues/1952 and
        https://github.com/hypothesis/lms/issues/3228).

        "Legacy" SpeedGrader submissions are ones from before we implemented
        this work-around, so they don't have the resource_link_id query param.
        """
        return self._is_speedgrader and not self._request.GET.get("resource_link_id")

    def sections_supported(self):
        """Return True if Canvas sections is supported for this request."""
        params = self._request.params
        if "focused_user" in params and "learner_canvas_user_id" not in params:
            # This is a legacy SpeedGrader URL, submitted to Canvas before our
            # Canvas course sections feature was released.
            return False

        try:
            application_instance = self._application_instance_service.get_current()
        except ApplicationInstanceNotFound:
            return False

        return bool(application_instance.developer_key)

    @property
    def sections_enabled(self):
        """Return True if Canvas sections is enabled for this request."""

        if not self.sections_supported():
            return False

        legacy_course, _ = self.get_or_create_course()

        return legacy_course.settings.get("canvas", "sections_enabled")

    def sync_api_config(self):
        if not self.sections_enabled or not self.is_group_launch:
            return None

        req = self._request
        sync_api_config = {
            "authUrl": req.route_url("canvas_api.oauth.authorize"),
            "path": req.route_path("canvas_api.sync"),
            "data": {
                "lms": {
                    "tool_consumer_instance_guid": req.params[
                        "tool_consumer_instance_guid"
                    ],
                },
                "course": {
                    "context_id": req.params["context_id"],
                    "custom_canvas_course_id": req.params["custom_canvas_course_id"],
                    "group_set": req.params.get("group_set"),
                },
                "group_info": {
                    key: value
                    for key, value in req.params.items()
                    if key in GroupInfo.columns()
                },
            },
        }

        if "learner_canvas_user_id" in req.params:
            sync_api_config["data"]["learner"] = {
                "canvas_user_id": req.params["learner_canvas_user_id"],
            }

        return sync_api_config
