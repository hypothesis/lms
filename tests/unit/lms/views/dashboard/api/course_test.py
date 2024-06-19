from unittest.mock import sentinel

import pytest
from sqlalchemy import select

from lms.models import Course
from lms.views.dashboard.api.course import CourseViews
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "course_service", "h_api", "organization_service", "dashboard_service"
)


class TestCourseViews:
    def test_get_courses(self, course_service, pyramid_request, views, get_page):
        courses = factories.Course.create_batch(5)
        get_page.return_value = courses, sentinel.pagination

        response = views.courses()

        course_service.get_courses.assert_called_once_with(
            pyramid_request.user.h_userid
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

    def test_get_organization_courses(
        self, course_service, pyramid_request, views, db_session, dashboard_service
    ):
        org = factories.Organization()
        courses = factories.Course.create_batch(5)
        dashboard_service.get_request_organization.return_value = org
        course_service.get_courses.return_value = select(Course)
        pyramid_request.matchdict["organization_public_id"] = sentinel.public_id
        db_session.flush()

        response = views.organization_courses()

        dashboard_service.get_request_organization.assert_called_once_with(
            pyramid_request
        )
        course_service.get_courses.assert_called_once_with(
            organization=org,
            h_userid=pyramid_request.user.h_userid,
        )
        course_service.get_courses_assignments_count.assert_called_once_with(courses)

        assert response == {
            "courses": [
                {
                    "id": c.id,
                    "title": c.lms_name,
                    "course_metrics": {
                        "assignments": course_service.get_courses_assignments_count.return_value.get.return_value,
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

    def test_course_assignments(
        self,
        views,
        pyramid_request,
        course_service,
        h_api,
        db_session,
        dashboard_service,
    ):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course = factories.Course()
        section = factories.CanvasSection(parent=course)
        dashboard_service.get_request_course.return_value = course

        assignment = factories.Assignment()
        assignment_with_no_annos = factories.Assignment()

        course_service.get_assignments.return_value = [
            assignment,
            assignment_with_no_annos,
        ]
        course_service.get_members.return_value = factories.User.create_batch(5)

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

        h_api.get_annotation_counts.return_value = stats

        response = views.course_assignments()

        h_api.get_annotation_counts.assert_called_once_with(
            [course.authority_provided_id, section.authority_provided_id],
            group_by="assignment",
            h_userids=[u.h_userid for u in course_service.get_members.return_value],
        )
        assert response == {
            "assignments": [
                {
                    "id": assignment.id,
                    "title": assignment.title,
                    "course": {
                        "id": course.id,
                        "title": course.lms_name,
                    },
                    "annotation_metrics": {
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
                    "annotation_metrics": {
                        "annotations": 0,
                        "replies": 0,
                        "last_activity": None,
                    },
                },
            ]
        }

    @pytest.fixture
    def views(self, pyramid_request):
        return CourseViews(pyramid_request)

    @pytest.fixture
    def get_page(self, patch):
        return patch("lms.views.dashboard.api.course.get_page")
