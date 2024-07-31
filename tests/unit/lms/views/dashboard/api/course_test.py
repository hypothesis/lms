from unittest.mock import sentinel

import pytest
from sqlalchemy import select

from lms.models import Course
from lms.views.dashboard.api.course import CourseViews
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "course_service",
    "h_api",
    "organization_service",
    "dashboard_service",
    "assignment_service",
)


class TestCourseViews:
    def test_get_courses(self, course_service, pyramid_request, views, get_page):
        courses = factories.Course.create_batch(5)
        get_page.return_value = courses, sentinel.pagination
        pyramid_request.parsed_params = {
            "h_userids": sentinel.h_userids,
            "assignment_ids": sentinel.assignment_ids,
        }

        response = views.courses()

        course_service.get_courses.assert_called_once_with(
            admin_organization_ids=[],
            instructor_h_userid=pyramid_request.user.h_userid,
            h_userids=sentinel.h_userids,
            assignment_ids=sentinel.assignment_ids,
        )
        get_page.assert_called_once_with(
            pyramid_request,
            course_service.get_courses.return_value,
            [Course.lms_name, Course.id],
        )
        assert response == {
            "courses": [{"id": c.id, "title": c.lms_name} for c in courses],
            "pagination": sentinel.pagination,
        }

    def test_course_metrics(
        self, course_service, pyramid_request, views, db_session, assignment_service
    ):
        courses = factories.Course.create_batch(5)
        course_service.get_courses.return_value = select(Course).order_by(Course.id)
        pyramid_request.matchdict["organization_public_id"] = sentinel.public_id
        pyramid_request.parsed_params = {
            "h_userids": sentinel.h_userids,
            "assignment_ids": sentinel.assignment_ids,
            "course_ids": sentinel.course_ids,
        }
        db_session.flush()

        response = views.courses_metrics()

        course_service.get_courses.assert_called_once_with(
            admin_organization_ids=[],
            instructor_h_userid=pyramid_request.user.h_userid,
            h_userids=sentinel.h_userids,
            assignment_ids=sentinel.assignment_ids,
            course_ids=sentinel.course_ids,
        )
        assignment_service.get_courses_assignments_count.assert_called_once_with(
            course_ids=[c.id for c in courses],
            admin_organization_ids=[],
            instructor_h_userid=pyramid_request.user.h_userid,
            h_userids=sentinel.h_userids,
            assignment_ids=sentinel.assignment_ids,
        )

        assert response == {
            "courses": [
                {
                    "id": c.id,
                    "title": c.lms_name,
                    "course_metrics": {
                        "assignments": assignment_service.get_courses_assignments_count.return_value.get.return_value,
                        "last_launched": c.updated.isoformat(),
                    },
                }
                for c in courses
            ]
        }

    def test_course(self, views, pyramid_request, dashboard_service):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course = factories.Course()
        dashboard_service.get_request_course.return_value = course

        response = views.course()

        dashboard_service.get_request_course.assert_called_once_with(pyramid_request)

        assert response == {
            "id": course.id,
            "title": course.lms_name,
        }

    @pytest.fixture
    def views(self, pyramid_request):
        return CourseViews(pyramid_request)

    @pytest.fixture
    def get_page(self, patch):
        return patch("lms.views.dashboard.api.course.get_page")
