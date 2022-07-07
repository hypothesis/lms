from lms.product.plugin import LTILaunchPlugin
from lms.services import HAPIError
from tests.unit.lms.resources.oauth2_redirect_test import JSConfig


class CanvasLTILaunchPlugin(LTILaunchPlugin):
    def __init__(self, request):
        self._request = request

    def add_to_launch_js_config(
        self, js_config: JSConfig, document_url, assignment_gradable
    ):
        # For students in Canvas with grades to submit we need to enable
        # Speedgrader settings for gradable assignments
        # `lis_result_sourcedid` associates a specific user with an
        # assignment.
        if (
            assignment_gradable
            and self._request.lti_user.is_learner
            and self._request.lti_params.get("lis_result_sourcedid")
        ):
            self._add_canvas_speedgrader_settings(js_config, document_url)

        # We add a `focused_user` query param to the SpeedGrader LTI launch
        # URLs we submit to Canvas for each student when the student
        # launches an assignment. Later, Canvas uses these URLs to launch
        # us when a teacher grades the assignment in SpeedGrader.
        if focused_user := self._request.params.get("focused_user"):
            js_config.set_focused_user(focused_user)

    def _add_canvas_speedgrader_settings(self, js_config, document_url):
        """
        Add config for students to record submissions with Canvas Speedgrader.

        This adds the config to call our `record_canvas_speedgrader_submission`
        API.

        :raise HTTPBadRequest: if a request param needed to generate the config
            is missing
        """
        lti_params = self._request.lti_params

        js_config._config["canvas"]["speedGrader"] = {
            "submissionParams": {
                "h_username": self._request.lti_user.h_user.username,
                "group_set": self._request.params.get("group_set"),
                "document_url": document_url,
                # Canvas doesn't send the right value for this on speed grader launches
                # sending instead the same value as for "context_id"
                "resource_link_id": lti_params.get("resource_link_id"),
                "lis_result_sourcedid": lti_params["lis_result_sourcedid"],
                "lis_outcome_service_url": lti_params["lis_outcome_service_url"],
                "learner_canvas_user_id": lti_params["custom_canvas_user_id"],
            },
        }

        # Enable the LMS frontend to receive notifications on annotation
        # activity. We'll use this information to only send the submission to
        # canvas on first annotation.
        if self._request.feature("submit_on_annotation"):
            # The `reportActivity` setting causes the front-end to make a call
            # back to the parent iframe for the specified events. The method in
            # the iframe happens to be called `reportActivity` too, but this is
            # a co-incidence. It could have any name.
            js_config._hypothesis_client["reportActivity"] = {
                "method": "reportActivity",
                "events": ["create", "update"],
            }

    def _set_focused_user(self, js_config, focused_user):
        """Configure the client to only show one users' annotations."""
        js_config._hypothesis_client["focus"] = {"user": {"username": focused_user}}

        # Unfortunately we need to pass the user's current display name to the
        # Hypothesis client, and we need to make a request to the h API to
        # retrieve that display name.
        try:
            display_name = (
                self._request.find_service(name="h_api")
                .get_user(focused_user)
                .display_name
            )
        except HAPIError:
            display_name = "(Couldn't fetch student name)"

        js_config._hypothesis_client["focus"]["user"]["displayName"] = display_name

    @classmethod
    def factory(cls, _context, request):
        return cls(request)
