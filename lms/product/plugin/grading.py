class GradingPlugin:
    @staticmethod
    def configure_grading_for_launch(request, js_config, assignment):
        """Configure grading during a launch."""
        if request.lti_user.is_instructor:
            # For instructors, display the toolbar
            js_config.enable_instructor_toolbar(enable_grading=assignment.is_gradable)
        else:
            # Create or update a record of LIS result data for a student launch
            # We'll query these rows to populate the student dropdown in the
            # instructor toolbar
            request.find_service(name="grading_info").upsert_from_request(request)
