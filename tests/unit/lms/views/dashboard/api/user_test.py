from unittest.mock import sentinel

import pytest
from sqlalchemy import select

from lms.js_config_types import APIStudent
from lms.models import RoleScope, RoleType, User
from lms.views.dashboard.api.user import UserViews
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "h_api", "assignment_service", "dashboard_service", "user_service"
)


class TestUserViews:
    def test_get_students(self, user_service, pyramid_request, views, get_page):
        pyramid_request.parsed_params = {
            "course_id": sentinel.course_id,
            "assignment_id": sentinel.assignment_id,
        }
        students = factories.User.create_batch(5)
        get_page.return_value = students, sentinel.pagination

        response = views.students()

        user_service.get_users.assert_called_once_with(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            instructor_h_userid=pyramid_request.user.h_userid,
            course_id=sentinel.course_id,
            assignment_id=sentinel.assignment_id,
        )
        get_page.assert_called_once_with(
            pyramid_request,
            user_service.get_users.return_value,
            [User.display_name, User.id],
        )
        assert response == {
            "students": [
                APIStudent(
                    {
                        "h_userid": c.h_userid,
                        "lms_id": c.user_id,
                        "display_name": c.display_name,
                    }
                )
                for c in students
            ],
            "pagination": sentinel.pagination,
        }

    def test_students_metrics(
        self, views, pyramid_request, user_service, h_api, dashboard_service, db_session
    ):
        # User returned by the stats endpoint
        student = factories.User(display_name="Bart")
        # User with no annotations
        student_no_annos = factories.User(display_name="Homer")
        # User with no annotations and no name
        student_no_annos_no_name = factories.User(display_name=None)

        pyramid_request.parsed_params = {
            "assignment_id": sentinel.id,
            "h_userids": sentinel.h_userids,
        }
        assignment = factories.Assignment()
        db_session.flush()
        user_service.get_users.return_value = select(User).where(
            User.id.in_(
                [u.id for u in [student, student_no_annos, student_no_annos_no_name]]
            )
        )
        dashboard_service.get_request_assignment.return_value = assignment
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

        response = views.students_metrics()

        dashboard_service.get_request_assignment.assert_called_once_with(
            pyramid_request
        )
        h_api.get_annotation_counts.assert_called_once_with(
            [g.authority_provided_id for g in assignment.groupings],
            group_by="user",
            resource_link_ids=[assignment.resource_link_id],
            h_userids=sentinel.h_userids,
        )
        expected = {
            "students": [
                {
                    "h_userid": student.h_userid,
                    "lms_id": student.user_id,
                    "display_name": student.display_name,
                    "annotation_metrics": {
                        "annotations": sentinel.annotations,
                        "replies": sentinel.replies,
                        "last_activity": sentinel.last_activity,
                    },
                },
                {
                    "h_userid": student_no_annos.h_userid,
                    "lms_id": student_no_annos.user_id,
                    "display_name": student_no_annos.display_name,
                    "annotation_metrics": {
                        "annotations": 0,
                        "replies": 0,
                        "last_activity": None,
                    },
                },
                {
                    "h_userid": student_no_annos_no_name.h_userid,
                    "lms_id": student_no_annos_no_name.user_id,
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
        return UserViews(pyramid_request)

    @pytest.fixture
    def get_page(self, patch):
        return patch("lms.views.dashboard.api.user.get_page")
