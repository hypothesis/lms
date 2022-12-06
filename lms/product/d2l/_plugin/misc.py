from lms.product.plugin.misc import MiscPlugin
from lms.services.lti_grading.interface import LTIGradingService


class D2LMiscPlugin(MiscPlugin):
    def __init__(self, settings: Settings):
        self._settings = settings

    def post_configure_assignment(self, request):
        """
        Run any actions needed after configuring an assignment.

        D2L doesn't create the container that holds grades (lineitems) LTI 1.3
        assignments.

        As a work-around, as soon as we configure the assignment on our end
        we'll use the LTIA grading API to create a new lineitem we can use
        later to record the grade.
        """
        lti_params = request.lti_params
        lti_grading_service = request.find_service(LTIGradingService)

        if not self._settings.create_lineitem:
            # No need to do anything if this option is off.
            return

        resource_link_id = lti_params.get("resource_link_id")
        resource_link_title = lti_params.get("resource_link_title")

        if not lti_grading_service.read_lineitems(
            lti_params.get("lineitems"), resource_link_id
        ):
            # If there are no existing lineitems, create one.
            lti_grading_service.create_lineitem(
                lti_params.get("lineitems"),
                resource_link_id,
                resource_link_title,
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

    @classmethod
    def factory(cls, _context, request):
        return cls(request.product.settings)
