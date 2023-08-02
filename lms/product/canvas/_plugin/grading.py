class CanvasGradingPlugin:
    @staticmethod
    def configure_grading_for_launch(request, js_config, assignment):
        """
        Configure grading during a launch.

        In canvas we use Speed Grader, we configure the frontend to use it.
        """
        lti_params = request.lti_params
        lti_user = request.lti_user

        # For students in Canvas with grades to submit we need to enable
        # Speedgrader settings for gradable assignments
        # `lis_result_sourcedid` associates a specific user with an
        # assignment.
        if (
            assignment.is_gradable
            and lti_user.is_learner
            and lti_params.get("lis_result_sourcedid")
        ):
            js_config.add_canvas_speedgrader_settings(assignment.document_url)

        # We add a `focused_user` query param to the LTI launch URL
        # we send to canvas with student submissions.
        # Later, when Canvas uses these URLs to launch
        # us when a teacher grades the assignment in SpeedGrader we read that value and
        # filter the annotations on the client to only show the ones by that student.
        if focused_user := request.params.get("focused_user"):
            js_config.set_focused_user(focused_user)

    @classmethod
    def factory(cls, _context, _request):
        return cls()
