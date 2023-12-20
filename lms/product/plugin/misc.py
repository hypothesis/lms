from lms.models import LTIParams, LTIRegistration
from lms.services.html_service import strip_html_tags


class MiscPlugin:
    """
    Plugin for product differences that don't have a better abstractions yet.

    Works as a placeholder location to centralize LMS differences here without
    the need to create bigger abstractions before it's clear what that
    abstraction should look like.

    The aim also includes to remove any checks around `product.family` around
    the code base.

    New methods here should not try to get a very tight API as easier to
    refactor once multiple LMSes have the same issue vs getting the right
    parameters in the first occurrence.

    Once any of these is implemented by more than one product or a group of
    methods looks like it could belong to their own plugin it's time to
    refactor them out.
    """

    # Whether or not to prompt for an assignment title while deep linking.
    deep_linking_prompt_for_title = True

    def post_launch_assignment_hook(
        self, request, js_config, assignment
    ):  # pragma: nocover
        """Run any actions needed for a successful launch of an assignment."""

    def accept_grading_comments(self, application_instance):
        """Whether to accept comments while grading."""
        # This is a LTI 1.3 only feature
        return application_instance.lti_version == "1.3.0"

    def clean_lms_grading_comment(self, comment: str) -> str:
        """Clean a comment coming from the LMS to display it in our grading comment textarea."""
        return strip_html_tags(comment)

    def format_grading_comment_for_lms(self, comment: str) -> str:
        """Format grading comment before sending it over via the API."""
        return comment

    def is_assignment_gradable(self, lti_params: LTIParams) -> bool:
        """Check if the assignment of the current launch is gradable."""
        return bool(lti_params.get("lis_outcome_service_url"))

    def get_ltia_aud_claim(self, lti_registration: LTIRegistration) -> str:
        """Get the value of the `aud` claim used in LTI advantage requests."""
        return lti_registration.token_url

    def get_document_url(self, request, assignment, historical_assignment):
        """Get a document URL from an assignment launch."""

        if assignment:
            return assignment.document_url

        if historical_assignment:
            return historical_assignment.document_url

        # Use the DL url as a fallback.
        return self.get_deep_linked_assignment_configuration(request).get("url")

    def get_deeplinking_launch_url(self, request, _assignment_configuration: dict):
        """
        Launch URL for deep linked assignments.

        To which URL to point the deep linked assignments in the LMS.
        This URL wel'll be part of the deep link response message
        to finish the configuration during a deep link request.
        """
        # In general we'll point to our regular basic launch URL.
        # The assignment configuration we'll be retrieved by other methods (eg, custom parameters) so that parameter is not used here.
        return request.route_url("lti_launches")

    def get_deep_linked_assignment_configuration(self, request):
        """Get the configuration of an assignment that was original deep linked."""
        params = {}
        possible_parameters = ["url", "group_set"]

        for param in possible_parameters:
            # Get the value from the custom parameters set during deep linking
            if value := request.lti_params.get(f"custom_{param}"):
                params[param] = value

        return params
