from unittest.mock import sentinel

import pytest
from sqlalchemy import select

from lms.models import Assignment, AutoGradingConfig, RoleScope, RoleType, User
from lms.views.dashboard.api.assignment import AssignmentViews
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "h_api", "assignment_service", "dashboard_service", "course_service", "user_service"
)


class TestAssignmentViews:
    def test_get_assignments(
        self, assignment_service, pyramid_request, views, get_page, db_session
    ):
        pyramid_request.parsed_params = {
            "course_ids": sentinel.course_ids,
            "h_userids": sentinel.h_userids,
        }
        assignments = factories.Assignment.create_batch(5)
        db_session.flush()  # Get IDs and create dates
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
            "assignments": [
                {"id": a.id, "title": a.title, "created": a.created}
                for a in assignments
            ],
            "pagination": sentinel.pagination,
        }

    def test_assignment(
        self,
        views,
        pyramid_request,
        assignment,
        db_session,
        dashboard_service,
        assignment_service,
    ):
        db_session.flush()
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        assignment_service.get_assignment_groups.return_value = []
        assignment_service.get_assignment_sections.return_value = []
        dashboard_service.get_request_assignment.return_value = assignment

        response = views.assignment()

        dashboard_service.get_request_assignment.assert_called_once_with(
            pyramid_request
        )

        assert response == {
            "id": assignment.id,
            "title": assignment.title,
            "created": assignment.created,
            "course": {"id": assignment.course.id, "title": assignment.course.lms_name},
        }

    def test_assignment_with_auto_grading(
        self, views, pyramid_request, assignment, db_session, dashboard_service
    ):
        assignment.auto_grading_config = AutoGradingConfig(
            activity_calculation="separate",
            grading_type="scaled",
            required_annotations=1,
            required_replies=1,
        )

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
            "created": assignment.created,
            "course": {"id": assignment.course.id, "title": assignment.course.lms_name},
            "groups": [],
            "auto_grading_config": {
                "activity_calculation": "separate",
                "grading_type": "scaled",
                "required_annotations": 1,
                "required_replies": 1,
            },
        }

    def test_assignment_with_groups(
        self, views, pyramid_request, assignment, dashboard_service, assignment_service
    ):
        groups = factories.CanvasGroup.create_batch(5)
        assignment_service.get_assignment_groups.return_value = groups
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        dashboard_service.get_request_assignment.return_value = assignment

        response = views.assignment()

        dashboard_service.get_request_assignment.assert_called_once_with(
            pyramid_request
        )
        assignment_service.get_assignment_groups.assert_called_once_with(assignment)

        assert response == {
            "id": assignment.id,
            "title": assignment.title,
            "created": assignment.created,
            "course": {"id": assignment.course.id, "title": assignment.course.lms_name},
            "groups": [
                {"h_authority_provided_id": g.authority_provided_id, "name": g.lms_name}
                for g in groups
            ],
        }

    def test_assignment_with_sections(
        self, views, pyramid_request, assignment, dashboard_service, assignment_service
    ):
        sections = factories.CanvasGroup.create_batch(5)
        assignment_service.get_assignment_groups.return_value = []
        assignment_service.get_assignment_sections.return_value = sections
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        dashboard_service.get_request_assignment.return_value = assignment

        response = views.assignment()

        dashboard_service.get_request_assignment.assert_called_once_with(
            pyramid_request
        )
        assignment_service.get_assignment_sections.assert_called_once_with(assignment)

        assert response == {
            "id": assignment.id,
            "title": assignment.title,
            "created": assignment.created,
            "course": {"id": assignment.course.id, "title": assignment.course.lms_name},
            "sections": [
                {"h_authority_provided_id": g.authority_provided_id, "name": g.lms_name}
                for g in sections
            ],
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
                    "created": assignment.created,
                    "course": {
                        "id": course.id,
                        "title": course.lms_name,
                    },
                    "annotation_metrics": {
                        "annotations": 4,
                        "replies": sentinel.replies,
                        "last_activity": sentinel.last_activity,
                    },
                },
                {
                    "id": assignment_with_no_annos.id,
                    "title": assignment_with_no_annos.title,
                    "created": assignment_with_no_annos.created,
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
    def assignments_metrics_response(self, assignment):
        return [
            {
                "assignment_id": assignment.resource_link_id,
                "annotations": 2,
                "page_notes": 2,
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
    def assignment(self, course, db_session):
        assignment = factories.Assignment(course=course)
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        db_session.flush()  # Get an ID and creation dates

        return assignment
