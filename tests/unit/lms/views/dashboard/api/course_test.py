from unittest.mock import sentinel

import pytest

from lms.views.dashboard.api.course import CourseViews
from tests import factories

pytestmark = pytest.mark.usefixtures("course_service")


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

    @pytest.fixture
    def views(self, pyramid_request):
        return CourseViews(pyramid_request)
