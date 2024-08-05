from unittest.mock import sentinel

import pytest
from sqlalchemy import select

from lms.models import Assignment, RoleScope, RoleType, User
from lms.views.dashboard.api.assignment import AssignmentViews
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "h_api", "assignment_service", "dashboard_service", "course_service", "user_service"
)


class TestAssignmentViews:
    def test_get_assignments(
        self, assignment_service, pyramid_request, views, get_page
    ):
        pyramid_request.parsed_params = {
            "course_ids": sentinel.course_ids,
            "h_userids": sentinel.h_userids,
        }
        assignments = factories.Assignment.create_batch(5)
        get_page.return_value = assignments, sentinel.pagination

        response = views.assignments()

        assignment_service.get_assignments.assert_called_once_with(
            instructor_h_userid=pyramid_request.user.h_userid,
            course_ids=sentinel.course_ids,
            h_userids=sentinel.h_userids,
            admin_organization_ids=[],
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
        self, views, pyramid_request, assignment, db_session, dashboard_service
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
            "course": {"id": assignment.course.id, "title": assignment.course.lms_name},
        }

    def test_course_assignments(
        self,
        views,
        pyramid_request,
        assignment_service,
        h_api,
        db_session,
        dashboard_service,
        user_service,
        assignments_metrics_response,
        assignment,
    ):
        pyramid_request.matchdict["course_id"] = sentinel.id
        pyramid_request.parsed_params = {"h_userids": sentinel.h_userids}
        course = factories.Course()
        section = factories.CanvasSection(parent=course)
        dashboard_service.get_request_course.return_value = course

        assignment_with_no_annos = factories.Assignment()
        users = factories.User.create_batch(5)
        db_session.flush()

        assignment_service.get_assignments.return_value = select(Assignment).where(
            Assignment.id.in_([assignment.id, assignment_with_no_annos.id])
        )
        user_service.get_users.return_value = (
            select(User).where(User.id.in_([u.id for u in users])).order_by(User.id)
        )
        h_api.get_annotation_counts.return_value = assignments_metrics_response

        response = views.course_assignments_metrics()

        user_service.get_users.assert_called_once_with(
            course_ids=[course.id],
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            instructor_h_userid=pyramid_request.user.h_userid,
            h_userids=sentinel.h_userids,
            admin_organization_ids=[],
        )
        h_api.get_annotation_counts.assert_called_once_with(
            [course.authority_provided_id, section.authority_provided_id],
            group_by="assignment",
            h_userids=[u.h_userid for u in users],
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

    def test_course_assignments_filtered_by_assignment_ids(
        self,
        views,
        pyramid_request,
        assignment_service,
        h_api,
        db_session,
        dashboard_service,
        user_service,
        assignment,
        assignments_metrics_response,
    ):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course = factories.Course()
        dashboard_service.get_request_course.return_value = course

        assignment_with_no_annos = factories.Assignment()
        users = factories.User.create_batch(5)
        db_session.flush()

        assignment_service.get_assignments.return_value = select(Assignment).where(
            Assignment.id.in_([assignment.id, assignment_with_no_annos.id])
        )
        user_service.get_users.return_value = (
            select(User).where(User.id.in_([u.id for u in users])).order_by(User.id)
        )

        h_api.get_annotation_counts.return_value = assignments_metrics_response
        pyramid_request.parsed_params = {"assignment_ids": [assignment.id]}

        response = views.course_assignments_metrics()

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
            ]
        }

    @pytest.fixture
    def assignments_metrics_response(self, assignment):
        return [
            {
                "assignment_id": assignment.resource_link_id,
                "annotations": sentinel.annotations,
                "replies": sentinel.replies,
                "userid": "TEACHER",
                "last_activity": sentinel.last_activity,
            },
        ]

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
        assignment = factories.Assignment(course=course)
        factories.AssignmentGrouping(assignment=assignment, grouping=course)

        return assignment
