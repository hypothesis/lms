from lms.models import Grouping


class GroupingServicePlugin:  # pragma: no cover
    group_type: Grouping.Type = None
    sections_type: Grouping.Type = None

    def get_sections_for_learner(self, _svc, _course):
        return None

    def get_sections_for_instructor(self, _svc, _course):
        return None

    def get_sections_for_grading(self, _svc, _course, _grading_student_id):
        return None

    def get_groups_for_learner(self, _svc, _course, _group_set_id):
        return None

    def get_groups_for_instructor(self, _svc, _course, _group_set_id):
        return None

    def get_groups_for_grading(self, _svc, _course, _group_set_id, _grading_student_id):
        return None
