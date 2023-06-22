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

    def get_document_url(self, request):
        """Get a document URL from an assignment launch."""

        # For assignments that don't use deep linking the source of truth for this information is our DB.
        assignment_service = request.find_service(name="assignment")

        assignment = assignment_service.get_assignment(
            tool_consumer_instance_guid=request.lti_params.get(
                "tool_consumer_instance_guid"
            ),
            resource_link_id=request.lti_params.get("resource_link_id"),
        )

        if not assignment:
            # If the current assignment is not yet in the DB maybe we
            # are launching for the first time a copied assignment.
            assignment = assignment_service.get_copied_from_assignment(
                request.lti_params
            )

        return assignment.document_url if assignment else None
