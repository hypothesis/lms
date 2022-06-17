from typing import List

from lms.models import Grouping


class GroupingPlugin:
    def __init__(self, user, lti_user):
        self._user = user
        self._lti_user = lti_user

    def get_groups(self, _course, _group_set_id, _grading_student_id) -> List[Grouping]:
        raise NotImplementedError

    def get_sections(self, course, grading_student_id) -> List[Grouping]:
        raise NotImplementedError

    def _to_groupings(
        self, type_, groupings: List[dict], parent=None
    ) -> List[Grouping]:
        groupings = self._grouping_service.upsert_groupings(
            groupings, parent=parent, type_=type_
        )
        self._grouping_service.upsert_grouping_memberships(self._user, groupings)
        return groupings
