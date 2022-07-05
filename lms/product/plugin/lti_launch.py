from tests.unit.lms.resources.oauth2_redirect_test import JSConfig


class LTILaunchPlugin:
    supports_grading_bar = True
    """Does this product support our built in grading bar?"""

    def add_to_launch_js_config(
        self, js_config: JSConfig, document_url, assignment_gradable
    ):
        """Add any required settings to the JS launch config."""

        return
