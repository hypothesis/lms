from urllib.parse import urlencode, urlparse

from pyramid.request import Request

from lms.models import LTIParams, LTIRegistration


class MiscPlugin:
    """
    Plugin for product differences that don't have a better abstractions yet.

    Works as a placeholder location to centralize LMS differences here without
    the need to create bigger abstractions before it's clear what that
    abstraction should look like.

    The aim also includes to remove any checks around `product.family` around
    the code base.

    New methods here should not try to get a very tight API as easier to
    refactor once multiple MS have the same issue vs getting the right
    parameters in the first occurrence.

    Once any of these is implemented by more than one product or a group of
    methods looks like it could belong to their own plugin it's time to
    refactor them out.
    """

    def post_configure_assignment(self, request: Request):  # pragma: nocover
        """
        Run any actions needed after configuring an assignment.

        This doesn't apply on deep linked setups where:
            - The exact moment of configuration is not know.
            - The deep linking message could include details about grading.
        """

    def is_assignment_gradable(self, lti_params: LTIParams) -> bool:
        """Check if the assignment of the current launch is gradable."""
        return bool(lti_params.get("lis_outcome_service_url"))

    def get_ltia_aud_claim(self, lti_registration: LTIRegistration) -> str:
        """Get the value of the `aud` claim used in LTI advantage requests."""
        return lti_registration.token_url

    def get_deeplinking_launch_url(self, request, params: dict):
        """
        Launch URL for deep linked assignments.

        After a deep linking request we must submit a deeplinking response back
        to the LMS pointing to which URL should be used in the launch.

        For LMSes that support query parameters in the launch URL we encode them there
        """

        return (
            urlparse(request.route_url("lti_launches"))
            ._replace(query=urlencode(params))
            .geturl()
        )
