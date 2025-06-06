from lms.product.plugin.misc import DeepLinkingPromptForGradableMixin, MiscPlugin


class D2LMiscPlugin(DeepLinkingPromptForGradableMixin, MiscPlugin):
    def get_ltia_aud_claim(self, lti_registration):  # noqa: ARG002
        # In D2L this value is always the same and different from
        # `lti_registration.token_url` as in other LMS
        return "https://api.brightspace.com/auth/token"

    @classmethod
    def factory(cls, _context, request):  # noqa: ARG003
        return cls()
