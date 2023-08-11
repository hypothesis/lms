from lms.product.plugin.misc import MiscPlugin


class BlackboardMiscPlugin(MiscPlugin):
    def accept_grading_comments(self, application_instance):
        # Blackboard doesn't return the existing comment on the grading API
        # preventing us from implementing this feature.
        return False

    @classmethod
    def factory(cls, _request, _context):
        return cls()
