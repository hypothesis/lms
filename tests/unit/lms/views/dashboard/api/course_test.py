from unittest.mock import sentinel

import pytest

from lms.views.dashboard.api.course import CourseViews
from tests import factories

pytestmark = pytest.mark.usefixtures("course_service", "h_api", "organization_service")


class TestCourseViews:
    def test_course(self, views, pyramid_request, course_service):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course = factories.Course()
        course_service.get_by_id.return_value = course

        response = views.course()

        course_service.get_by_id.assert_called_once_with(sentinel.id)

        assert response == {
            "id": course.id,
            "title": course.lms_name,
        }

    def test_course_stats(
        self, views, pyramid_request, course_service, h_api, db_session
    ):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course = factories.Course()
        section = factories.CanvasSection(parent=course)
        course_service.get_by_id.return_value = course

        assignment = factories.Assignment()
        assignment_with_no_annos = factories.Assignment()

        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        factories.AssignmentGrouping(
            assignment=assignment_with_no_annos, grouping=course
        )
        db_session.flush()

        stats = [
            {
                "assignment_id": assignment.resource_link_id,
                "annotations": sentinel.annotations,
                "replies": sentinel.replies,
                "userid": "TEACHER",
                "last_activity": sentinel.last_activity,
            },
        ]

        h_api.get_course_stats.return_value = stats

        response = views.course_stats()

        h_api.get_course_stats.assert_called_once_with(
            [course.authority_provided_id, section.authority_provided_id]
        )
        assert response == [
            {
                "id": assignment.id,
                "title": assignment.title,
                "course": {
                    "id": course.id,
                    "title": course.lms_name,
                },
                "stats": {
                    "annotations": sentinel.annotations,
                    "replies": sentinel.replies,
                    "last_activity": sentinel.last_activity,
                },
            },
            {
                "id": assignment_with_no_annos.id,
                "title": assignment_with_no_annos.title,
                "course": {
                    "id": course.id,
                    "title": course.lms_name,
                },
                "stats": {
                    "annotations": 0,
                    "replies": 0,
                    "last_activity": None,
                },
            },
        ]

    @pytest.fixture
    def views(self, pyramid_request):
        return CourseViews(pyramid_request)
