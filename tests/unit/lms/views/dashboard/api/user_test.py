from unittest.mock import call, sentinel

import pytest
from sqlalchemy import select

from lms.js_config_types import APIStudent
from lms.models import AutoGradingConfig, RoleScope, RoleType, User
from lms.views.dashboard.api.user import UserViews
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "h_api", "assignment_service", "dashboard_service", "user_service"
)


class TestUserViews:
    def test_get_students(self, user_service, pyramid_request, views, get_page):
        pyramid_request.parsed_params = {
            "course_ids": sentinel.course_ids,
            "assignment_ids": sentinel.assignment_ids,
            "segment_authority_provided_ids": sentinel.segment_authority_provided_ids,
        }
        students = factories.User.create_batch(5)
        get_page.return_value = students, sentinel.pagination

        response = views.students()

        user_service.get_users.assert_called_once_with(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            instructor_h_userid=pyramid_request.user.h_userid,
            admin_organization_ids=[],
            course_ids=sentinel.course_ids,
            assignment_ids=sentinel.assignment_ids,
            segment_authority_provided_ids=sentinel.segment_authority_provided_ids,
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

    @pytest.mark.parametrize("with_auto_grading", [True, False])
    @pytest.mark.parametrize("with_segment_authority_provided_id", [True, False])
    def test_students_metrics(  # pylint:disable=too-many-locals
        self,
        views,
        pyramid_request,
        user_service,
        h_api,
        dashboard_service,
        db_session,
        with_auto_grading,
        with_segment_authority_provided_id,
        calculate_grade,
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
        assignment = factories.Assignment(course=factories.Course())
        if with_segment_authority_provided_id:
            segments = factories.CanvasSection.create_batch(
                5, parent_id=assignment.course_id
            )
            for segment in segments:
                factories.AssignmentGrouping(assignment=assignment, grouping=segment)
            db_session.flush()
            pyramid_request.parsed_params["segment_authority_provided_ids"] = [
                g.authority_provided_id for g in segments
            ]

        if with_auto_grading:
            assignment.auto_grading_config = AutoGradingConfig(
                activity_calculation="separate",
                grading_type="all_or_nothing",
                required_annotations=1,
            )

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
                "annotations": 2,
                "page_notes": 2,
                "replies": sentinel.replies,
                "userid": student.h_userid,
                "last_activity": sentinel.last_activity,
            },
            {
                "display_name": sentinel.display_name,
                "annotations": sentinel.annotations,
                "page_notes": sentinel.page_notes,
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
                        "annotations": 4,
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

        if with_auto_grading:
            calls = []
            for student in expected["students"]:
                student["auto_grading_grade"] = calculate_grade.return_value
                calls.append(
                    call(assignment.auto_grading_config, student["annotation_metrics"])
                )

            calculate_grade.assert_has_calls(calls)

        assert response == expected

    @pytest.fixture
    def views(self, pyramid_request):
        return UserViews(pyramid_request)

    @pytest.fixture
    def get_page(self, patch):
        return patch("lms.views.dashboard.api.user.get_page")

    @pytest.fixture
    def calculate_grade(self, patch):
        return patch("lms.views.dashboard.api.user.calculate_grade")
