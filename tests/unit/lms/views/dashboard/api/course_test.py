import json
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models import Course
from lms.validation import ValidationError
from lms.views.dashboard.api.course import CourseViews, ListCoursesSchema
from tests import factories

pytestmark = pytest.mark.usefixtures("course_service", "h_api", "organization_service")


class TestCourseViews:
    def test_get_courses(self, course_service, pyramid_request, views, db_session):
        pyramid_request.parsed_params = {"limit": 100}
        courses = factories.Course.create_batch(5)
        course_service.get_courses.return_value = db_session.query(Course)
        db_session.flush()

        response = views.courses()

        course_service.get_courses.assert_called_once_with(
            h_userid=pyramid_request.user.h_userid,
        )
        assert response == {
            "courses": [{"id": c.id, "title": c.lms_name} for c in courses],
            "pagination": {"next": None},
        }

    def test_get_courses_empty(
        self, course_service, pyramid_request, views, db_session
    ):
        pyramid_request.parsed_params = {"limit": 100}
        course_service.get_courses.return_value = db_session.query(Course)

        response = views.courses()

        course_service.get_courses.assert_called_once_with(
            h_userid=pyramid_request.user.h_userid,
        )
        assert response == {
            "courses": [],
            "pagination": {"next": None},
        }

    def test_get_courses_with_cursor(
        self, course_service, pyramid_request, views, db_session
    ):
        courses = sorted(factories.Course.create_batch(10), key=lambda c: c.lms_name)
        db_session.flush()
        course_service.get_courses.return_value = db_session.query(Course).order_by(
            Course.lms_name, Course.id
        )

        pyramid_request.params = {"limit": 1}
        pyramid_request.parsed_params = {
            "limit": 1,
            "cursor": (courses[4].lms_name, courses[4].id),
        }

        response = views.courses()

        course_service.get_courses.assert_called_once_with(
            h_userid=pyramid_request.user.h_userid,
        )
        assert response == {
            "courses": [{"id": c.id, "title": c.lms_name} for c in courses[5:6]],
            "pagination": {
                "next": Any.url.with_path("/api/dashboard/courses").with_query(
                    {"cursor": Any.string(), "limit": "1"}
                )
            },
        }

    def test_get_courses_next_doesnt_include_limit_if_not_in_original_request(
        self, course_service, pyramid_request, views, db_session
    ):
        courses = sorted(factories.Course.create_batch(10), key=lambda c: c.lms_name)
        db_session.flush()
        course_service.get_courses.return_value = db_session.query(Course).order_by(
            Course.lms_name, Course.id
        )

        pyramid_request.parsed_params = {
            "limit": 1,
            "cursor": (courses[4].lms_name, courses[4].id),
        }

        response = views.courses()

        course_service.get_courses.assert_called_once_with(
            h_userid=pyramid_request.user.h_userid,
        )
        assert response == {
            "courses": [{"id": c.id, "title": c.lms_name} for c in courses[5:6]],
            "pagination": {
                "next": Any.url.with_path("/api/dashboard/courses").with_query(
                    {"cursor": Any.string()}
                )
            },
        }

    def test_get_organization_courses(
        self, course_service, organization_service, pyramid_request, views, db_session
    ):
        org = factories.Organization()
        courses = factories.Course.create_batch(5)
        organization_service.get_by_public_id.return_value = org
        course_service.get_courses.return_value = courses
        pyramid_request.matchdict["organization_public_id"] = sentinel.public_id
        db_session.flush()

        response = views.organization_courses()

        organization_service.get_by_public_id.assert_called_once_with(
            sentinel.public_id
        )
        course_service.get_courses.assert_called_once_with(
            organization=org,
            h_userid=pyramid_request.user.h_userid,
        )
        course_service.get_courses_assignments_count.assert_called_once_with(
            course_service.get_courses.return_value
        )

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

    def test_course_assignments(
        self, views, pyramid_request, course_service, h_api, db_session
    ):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course = factories.Course()
        section = factories.CanvasSection(parent=course)
        course_service.get_by_id.return_value = course

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


class TestListCoursesSchema:
    def test_limit_default(self, pyramid_request):
        assert ListCoursesSchema(pyramid_request).parse() == {"limit": 100}

    def test_invalid_cursor(self, pyramid_request):
        pyramid_request.GET = {"cursor": "NOPE"}

        with pytest.raises(ValidationError):
            ListCoursesSchema(pyramid_request).parse()

    def test_cursor(self, pyramid_request):
        pyramid_request.GET = {"cursor": json.dumps(("VALUE", "OTHER_VALUE"))}

        assert ListCoursesSchema(pyramid_request).parse() == {
            "limit": 100,
            "cursor": ["VALUE", "OTHER_VALUE"],
        }
