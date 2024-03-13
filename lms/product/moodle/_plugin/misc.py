from lms.product.plugin.misc import MiscPlugin


class MoodleMiscPlugin(MiscPlugin):
    @classmethod
    def factory(cls, _context, request):  # pragma: no cover
        return cls()
