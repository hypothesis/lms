from lms.product.plugin.misc import MiscPlugin
from lms.services.lti_grading.interface import LTIGradingService


class D2LMiscPlugin(MiscPlugin):
    def __init__(self, create_line_item: bool):
        self._create_line_item = create_line_item

    def post_configure_assignment(self, request):
        """
        Run any actions needed after configuring an assignment.

        D2L doesn't create the container that holds grades (line item) LTI 1.3
        assignments.

        As a work-around, as soon as we configure the assignment on our end
        we'll use the LTIA grading API to create a new line item we can use
        later to record the grade.
        """
        # Nothing to do if line item creation is off, or it's already there
        if not self._create_line_item or super().is_assignment_gradable(
            request.lti_params
        ):
            return

        request.find_service(LTIGradingService).create_line_item(
            resource_link_id=request.lti_params.get("resource_link_id"),
            label=request.lti_params.get("resource_link_title"),
        )

    def is_assignment_gradable(self, lti_params):
        """Check if the assignment of the current launch is gradable."""
        if self._create_line_item and lti_params["lti_version"] == "1.3.0":
            # D2L doesn't automatically create a line item for assignments by
            # default like it does for 1.1. If we are creating them
            # automatically all assignments will be gradable.
            return True

        return super().is_assignment_gradable(lti_params)

    def get_ltia_aud_claim(self, lti_registration):
        # In D2L this value is always the same and different from
        # `lti_registration.token_url` as in other LMS
        return "https://api.brightspace.com/auth/token"

    def get_document_url(self, request, assignment, historical_assignment):
        url = super().get_document_url(request, assignment, historical_assignment)

        if not url:
            # In D2L support both deep linking and DB backed assignment.
            # Use the DL url as a fallback.
            url = self.get_deep_linked_assignment_configuration(request).get("url")

        return url

    @classmethod
    def factory(cls, _context, request):
        return cls(request.product.settings.custom.get("create_line_item", False))
