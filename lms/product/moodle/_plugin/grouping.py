from lms.product.plugin.grouping import GroupError, GroupingPlugin


class MoodleGroupingPlugin(GroupingPlugin):
    def __init__(self, api):
        self._api = api

    @classmethod
    def factory(cls, _context, request):
        return cls(api=request.find_service(MoodleAPIClient))
