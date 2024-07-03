from unittest.mock import sentinel

import pytest

from lms.models import Assignment
from lms.views.dashboard.api.assignment import AssignmentViews
from tests import factories

pytestmark = pytest.mark.usefixtures("h_api", "assignment_service", "dashboard_service")


class TestAssignmentViews:
    def test_get_assignments(
        self, assignment_service, pyramid_request, views, get_page
    ):
        pyramid_request.parsed_params = {"course_id": sentinel.course_id}
        assignments = factories.Assignment.create_batch(5)
        get_page.return_value = assignments, sentinel.pagination

        response = views.assignments()

        assignment_service.get_assignments.assert_called_once_with(
            pyramid_request.user.h_userid, course_id=sentinel.course_id
        )
        get_page.assert_called_once_with(
            pyramid_request,
            assignment_service.get_assignments.return_value,
            [Assignment.title, Assignment.id],
        )
        assert response == {
            "assignments": [{"id": a.id, "title": a.title} for a in assignments],
            "pagination": sentinel.pagination,
        }

    def test_assignment(
        self, views, pyramid_request, course, assignment, db_session, dashboard_service
    ):
        db_session.flush()
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        dashboard_service.get_request_assignment.return_value = assignment

        response = views.assignment()

        dashboard_service.get_request_assignment.assert_called_once_with(
            pyramid_request
        )

        assert response == {
            "id": assignment.id,
            "title": assignment.title,
            "course": {"id": course.id, "title": course.lms_name},
        }

    @pytest.fixture
    def views(self, pyramid_request):
        return AssignmentViews(pyramid_request)

    @pytest.fixture
    def course(self):
        return factories.Course()

    @pytest.fixture
    def get_page(self, patch):
        return patch("lms.views.dashboard.api.assignment.get_page")

    @pytest.fixture
    def assignment(self, course):
        assignment = factories.Assignment()
        factories.AssignmentGrouping(assignment=assignment, grouping=course)

        return assignment
