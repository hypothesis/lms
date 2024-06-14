from unittest.mock import sentinel

import pytest

from lms.views.dashboard.api.assignment import AssignmentViews
from tests import factories

pytestmark = pytest.mark.usefixtures("h_api", "assignment_service")


class TestAssignmentViews:
    def test_assignment(
        self, views, pyramid_request, assignment_service, course, assignment, db_session
    ):
        db_session.flush()
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        assignment_service.get_by_id.return_value = assignment

        response = views.assignment()

        assignment_service.get_by_id.assert_called_once_with(sentinel.id)

        assert response == {
            "id": assignment.id,
            "title": assignment.title,
            "course": {"id": course.id, "title": course.lms_name},
        }

    def test_assignment_stats(self, views, pyramid_request, assignment_service, h_api):
        # User returned by the stats endpoint
        student = factories.User(display_name="Bart")
        # User with no annotations
        student_no_annos = factories.User(display_name="Homer")
        # User with no annotations and no name
        student_no_annos_no_name = factories.User(display_name=None)

        pyramid_request.matchdict["assignment_id"] = sentinel.id
        assignment = factories.Assignment()
        assignment_service.get_members.return_value = [
            student,
            student_no_annos,
            student_no_annos_no_name,
        ]
        assignment_service.get_by_id.return_value = assignment
        stats = [
            {
                "display_name": student.display_name,
                "annotations": sentinel.annotations,
                "replies": sentinel.replies,
                "userid": student.h_userid,
                "last_activity": sentinel.last_activity,
            },
            {
                "display_name": sentinel.display_name,
                "annotations": sentinel.annotations,
                "replies": sentinel.replies,
                "userid": "TEACHER",
                "last_activity": sentinel.last_activity,
            },
        ]

        h_api.get_annotation_counts.return_value = stats

        response = views.assignment_stats()

        assignment_service.get_by_id.assert_called_once_with(sentinel.id)
        h_api.get_annotation_counts.assert_called_once_with(
            [g.authority_provided_id for g in assignment.groupings],
            group_by="user",
            resource_link_id=assignment.resource_link_id,
        )
        expected = {
            "students": [
                {
                    "id": student.user_id,
                    "display_name": student.display_name,
                    "annotation_metrics": {
                        "annotations": sentinel.annotations,
                        "replies": sentinel.replies,
                        "last_activity": sentinel.last_activity,
                    },
                },
                {
                    "id": student_no_annos.user_id,
                    "display_name": student_no_annos.display_name,
                    "annotation_metrics": {
                        "annotations": 0,
                        "replies": 0,
                        "last_activity": None,
                    },
                },
                {
                    "id": student_no_annos_no_name.user_id,
                    "display_name": None,
                    "annotation_metrics": {
                        "annotations": 0,
                        "replies": 0,
                        "last_activity": None,
                    },
                },
            ]
        }
        assert response == expected

    @pytest.fixture
    def views(self, pyramid_request):
        return AssignmentViews(pyramid_request)

    @pytest.fixture
    def course(self):
        return factories.Course()

    @pytest.fixture
    def assignment(self, course):
        assignment = factories.Assignment()
        factories.AssignmentGrouping(assignment=assignment, grouping=course)

        return assignment
