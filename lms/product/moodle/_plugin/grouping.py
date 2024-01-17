from lms.models import Course, Grouping
from lms.product.plugin.grouping import GroupError, GroupingPlugin
from lms.services.moodle import MoodleAPIClient


class MoodleGroupingPlugin(GroupingPlugin):
    group_type = Grouping.Type.MOODLE_GROUP

    def __init__(self, api):
        self._api = api

    def get_group_sets(self, course: Course):
        group_sets = self._api.course_group_sets(course.lms_id)
        course.set_group_sets(group_sets)
        return group_sets

    @classmethod
    def factory(cls, _context, request):
        return cls(api=request.find_service(MoodleAPIClient))
