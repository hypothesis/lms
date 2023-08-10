from lms.product.plugin.misc import MiscPlugin
from lms.services.lti_grading.interface import LTIGradingService


class D2LMiscPlugin(MiscPlugin):
    # Deep linking in D2L implies creating a new assignment.
    # Prompt for a title to set it for the new assignment.
    deep_linking_prompt_for_title = True

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
        return cls()
