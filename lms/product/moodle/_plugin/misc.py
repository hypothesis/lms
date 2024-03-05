from lms.product.plugin.misc import MiscPlugin


class MoodleMiscPlugin(MiscPlugin):
    deep_linking_prompt_for_title = False
    # Moodle's deep linking flow it's included in the activity creating one.
    # Removing our title prompt to avoid confusion with the one in the LMS.

    @classmethod
    def factory(cls, _context, request):  # pragma: no cover
        return cls()
