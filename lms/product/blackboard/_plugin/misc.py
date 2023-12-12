from lms.product.plugin.misc import MiscPlugin


class BlackboardMiscPlugin(MiscPlugin):
    def format_grading_comment_for_lms(self, comment: str) -> str:
        # Replace new lines by by html, otherwise format it lost when read back.
        return comment.replace("\n", "<br/>")

    @classmethod
    def factory(cls, _request, _context):
        return cls()
