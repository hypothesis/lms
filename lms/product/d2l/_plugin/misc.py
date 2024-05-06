from lms.product.plugin.misc import MiscPlugin


class D2LMiscPlugin(MiscPlugin):
    def get_ltia_aud_claim(self, lti_registration):
        # In D2L this value is always the same and different from
        # `lti_registration.token_url` as in other LMS
        return "https://api.brightspace.com/auth/token"

    @classmethod
    def factory(cls, _context, request):
        return cls()
