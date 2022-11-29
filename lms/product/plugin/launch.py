# pylint: disable=unused-argument
class LaunchPlugin:
    def is_assignment_gradable(self, lti_params):
        """Check if the assignment of the current launch is gradable."""
        return bool(lti_params.get("lis_outcome_service_url"))

    def course_extra(self, lti_params):
        """Extra information to store for courses."""
        return {}
