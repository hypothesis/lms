from lms.models import ApplicationInstance
from lms.product.plugin.misc import MiscPlugin


class D2LMiscPlugin(MiscPlugin):
    def deep_linking_prompt_for_gradable(
        self, application_instance: ApplicationInstance
    ) -> bool:
        """
        Whether or not to ask if the new assignment should be gradable.

        We'll only prompt for gradable assignments in D2L if the
        `HYPOTHESIS_PROMPT_FOR_GRADABLE` setting is enabled and we are in LTI1.3
        """
        if application_instance.lti_version == "LTI-1p0":
            return False

        ai_settings = application_instance.settings
        return ai_settings.get_setting(
            ai_settings.fields[ai_settings.Settings.HYPOTHESIS_PROMPT_FOR_GRADABLE]
        )

    def get_ltia_aud_claim(self, lti_registration):  # noqa: ARG002
        # In D2L this value is always the same and different from
        # `lti_registration.token_url` as in other LMS
        return "https://api.brightspace.com/auth/token"

    @classmethod
    def factory(cls, _context, request):  # noqa: ARG003
        return cls()
