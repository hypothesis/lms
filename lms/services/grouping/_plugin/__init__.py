class GroupingServicePlugin:
    group_type: Grouping.Type = None
    sections_type: Grouping.Type = None

    def get_sections_for_learner(self, svc, course):
        return None

    def get_sections_for_instructor(self, svc, course):
        return None

    def get_sections_for_grading(self, svc, course, grading_student_id):
        return None

    def get_groups_for_learner(self, svc, course, group_set_id):
        return None

    def get_groups_for_instructor(self, svc, course, group_set_id):
        return None

    def get_groups_for_grading(self, svc, course, group_set_id, grading_student_id):
        return None
