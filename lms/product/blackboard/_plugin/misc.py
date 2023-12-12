from lms.product.plugin.misc import MiscPlugin


class BlackboardMiscPlugin(MiscPlugin):
    @classmethod
    def factory(cls, _request, _context):
        return cls()
