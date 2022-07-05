from tests.unit.lms.resources.oauth2_redirect_test import JSConfig


class LTILaunchPlugin:
    supports_grading_bar = True

    def __init__(self, request):
        self._request = request

    def add_to_launch_js_config(
        self, js_config: JSConfig, document_url, assignment_gradable
    ):
        """Add any required settings to the JS launch config."""

        # For students in Canvas with grades to submit we need to enable
        # Speedgrader settings for gradable assignments
        # `lis_result_sourcedid` associates a specific user with an
        # assignment.
        if (
            assignment_gradable
            and self._request.lti_user.is_learner
            and self._request.lti_params.get("lis_result_sourcedid")
        ):
            js_config.add_canvas_speedgrader_settings(document_url)

        # We add a `focused_user` query param to the SpeedGrader LTI launch
        # URLs we submit to Canvas for each student when the student
        # launches an assignment. Later, Canvas uses these URLs to launch
        # us when a teacher grades the assignment in SpeedGrader.
        if focused_user := self._request.params.get("focused_user"):
            js_config.set_focused_user(focused_user)

    @classmethod
    def factory(cls, _context, request):
        return cls(request)
