from datetime import datetime
from unittest.mock import call, patch, sentinel

import pytest
from sqlalchemy import select

from lms.js_config_types import APIStudent
from lms.models import AutoGradingConfig, LMSUser, RoleScope, RoleType, User
from lms.views.dashboard.api.user import UserViews
from tests import factories

pytestmark = pytest.mark.usefixtures(
    "h_api",
    "assignment_service",
    "dashboard_service",
    "user_service",
    "auto_grading_service",
)


class TestUserViews:
    @pytest.mark.parametrize("segment_authority_provided_ids", [None, [sentinel.id]])
    def test_get_students(
        self,
        pyramid_request,
        views,
        get_page,
        segment_authority_provided_ids,
        _students_query,  # noqa: PT019
    ):
        pyramid_request.parsed_params = {
            "course_ids": [sentinel.course_id_1, sentinel.course_id_2],
            "assignment_ids": [sentinel.assignment_id_1, sentinel.assignment_id_2],
            "segment_authority_provided_ids": segment_authority_provided_ids,
        }
        students = factories.LMSUser.create_batch(5)
        get_page.return_value = students, sentinel.pagination

        _students_query.return_value = (sentinel.last_updated, sentinel.query)

        response = views.students()

        get_page.assert_called_once_with(
            pyramid_request, sentinel.query, [LMSUser.display_name, LMSUser.id]
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

    @pytest.mark.parametrize("with_segment_authority_provided_id", [True, False])
    def test_students_metrics(
        self,
        views,
        pyramid_request,
        h_api,
        dashboard_service,
        db_session,
        with_segment_authority_provided_id,
        annotation_counts_response,
        student,
    ):
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
            dashboard_service.get_request_segment.return_value = segments

            dashboard_service.get_segments_roster.return_value = (
                None,
                select(User)
                .where(
                    User.id.in_(
                        [
                            u.id
                            for u in [
                                student,
                                student_no_annos,
                                student_no_annos_no_name,
                            ]
                        ]
                    )
                )
                .add_columns(True),  # noqa: FBT003
            )

        else:
            db_session.flush()
            dashboard_service.get_assignment_roster.return_value = (
                None,
                select(User)
                .where(
                    User.id.in_(
                        [
                            u.id
                            for u in [
                                student,
                                student_no_annos,
                                student_no_annos_no_name,
                            ]
                        ]
                    )
                )
                .add_columns(True),  # noqa: FBT003
            )

        db_session.flush()

        dashboard_service.get_request_assignment.return_value = assignment
        h_api.get_annotation_counts.return_value = annotation_counts_response

        response = views.students_metrics()

        dashboard_service.get_request_assignment.assert_has_calls(
            [call(pyramid_request, sentinel.id)]
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
                    "active": True,
                    "h_userid": student.h_userid,
                    "lms_id": student.user_id,
                    "display_name": student.display_name,
                    "annotation_metrics": {
                        "annotations": 4,
                        "replies": sentinel.replies,
                        "last_activity": datetime(2024, 1, 1),  # noqa: DTZ001
                    },
                },
                {
                    "active": True,
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
                    "active": True,
                    "h_userid": student_no_annos_no_name.h_userid,
                    "lms_id": student_no_annos_no_name.user_id,
                    "display_name": None,
                    "annotation_metrics": {
                        "annotations": 0,
                        "replies": 0,
                        "last_activity": None,
                    },
                },
            ],
            "last_updated": None,
        }
        assert response == expected

    @pytest.mark.parametrize("with_last_grade", [True, False])
    def test_students_metrics_with_auto_grading(
        self,
        views,
        pyramid_request,
        h_api,
        student,
        dashboard_service,
        db_session,
        auto_grading_service,
        annotation_counts_response,
        with_last_grade,
    ):
        # User with no annotations
        student_no_annos = factories.User(display_name="Homer")
        # User with no annotations and no name
        student_no_annos_no_name = factories.User(display_name=None)

        pyramid_request.parsed_params = {
            "h_userids": sentinel.h_userids,
            "assignment_id": sentinel.assignment_id,
        }
        assignment = factories.Assignment(course=factories.Course())
        assignment.auto_grading_config = AutoGradingConfig(
            activity_calculation="separate",
            grading_type="all_or_nothing",
            required_annotations=1,
        )

        if not with_last_grade:
            auto_grading_service.get_last_grades.return_value = {}

        db_session.flush()
        dashboard_service.get_assignment_roster.return_value = (
            None,
            select(User)
            .where(
                User.id.in_(
                    [
                        u.id
                        for u in [student, student_no_annos, student_no_annos_no_name]
                    ]
                )
            )
            .add_columns(True),  # noqa: FBT003
        )
        dashboard_service.get_request_assignment.return_value = assignment
        h_api.get_annotation_counts.return_value = annotation_counts_response

        response = views.students_metrics()

        dashboard_service.get_request_assignment.assert_has_calls(
            [
                call(pyramid_request, sentinel.assignment_id),
                call(pyramid_request, assignment.id),
            ]
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
                    "active": True,
                    "h_userid": student.h_userid,
                    "lms_id": student.user_id,
                    "display_name": student.display_name,
                    "annotation_metrics": {
                        "annotations": 4,
                        "replies": sentinel.replies,
                        "last_activity": datetime(2024, 1, 1),  # noqa: DTZ001
                    },
                },
                {
                    "active": True,
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
                    "active": True,
                    "h_userid": student_no_annos_no_name.h_userid,
                    "lms_id": student_no_annos_no_name.user_id,
                    "display_name": None,
                    "annotation_metrics": {
                        "annotations": 0,
                        "replies": 0,
                        "last_activity": None,
                    },
                },
            ],
            "last_updated": None,
        }
        calls = []

        last_grades = auto_grading_service.get_last_grades.return_value
        for api_student in expected["students"]:
            api_student["auto_grading_grade"] = {
                "current_grade": auto_grading_service.calculate_grade.return_value,
                "last_grade": last_grades.get.return_value.grade
                if with_last_grade
                else None,
                "last_grade_date": last_grades.get.return_value.updated
                if with_last_grade
                else None,
            }
            calls.append(
                call(
                    assignment.auto_grading_config,
                    api_student["annotation_metrics"],
                )
            )

        auto_grading_service.calculate_grade.assert_has_calls(calls)

        assert response == expected

    def test__students_query_single_course(
        self, views, pyramid_request, dashboard_service
    ):
        pyramid_request.parsed_params = {"course_ids": [sentinel.course_id]}

        views._students_query(assignment_ids=None, segment_authority_provided_ids=None)  # noqa: SLF001

        dashboard_service.get_request_course.assert_called_once_with(
            pyramid_request, sentinel.course_id
        )
        dashboard_service.get_course_roster.assert_called_once_with(
            lms_course=dashboard_service.get_request_course.return_value.lms_course,
            h_userids=None,
        )

    def test__students_query_fallback_launch_data(
        self, views, pyramid_request, user_service
    ):
        pyramid_request.parsed_params = {
            "course_ids": [sentinel.course_id, sentinel.course_id_2]
        }

        views._students_query(assignment_ids=None, segment_authority_provided_ids=None)  # noqa: SLF001

        user_service.get_users.assert_called_once_with(
            include_role=(RoleScope.COURSE, RoleType.LEARNER),
            course_ids=[sentinel.course_id, sentinel.course_id_2],
            assignment_ids=None,
            instructor_h_userid=pyramid_request.user.h_userid,
            admin_organization_ids=[],
            h_userids=None,
            segment_authority_provided_ids=None,
        )

    def test__students_query_organization(self, views, user_service, pyramid_request):
        views._students_query(assignment_ids=None, segment_authority_provided_ids=None)  # noqa: SLF001

        user_service.get_users_for_organization.assert_called_once_with(
            include_role=(RoleScope.COURSE, RoleType.LEARNER),
            h_userids=None,
            instructor_h_userid=pyramid_request.user.h_userid,
            admin_organization_ids=[],
        )

    @pytest.fixture
    def views(self, pyramid_request):
        pyramid_request.parsed_params = {}
        return UserViews(pyramid_request)

    @pytest.fixture
    def student(self):
        return factories.User(display_name="Bart")

    @pytest.fixture
    def annotation_counts_response(self, student):
        return [
            {
                "display_name": student.display_name,
                "annotations": 2,
                "page_notes": 2,
                "replies": sentinel.replies,
                "userid": student.h_userid,
                "last_activity": "2024-01-01",
            },
            {
                "display_name": sentinel.display_name,
                "annotations": sentinel.annotations,
                "page_notes": sentinel.page_notes,
                "replies": sentinel.replies,
                "userid": "TEACHER",
                "last_activity": "2024-01-02",
            },
        ]

    @pytest.fixture
    def _students_query(self, views):
        with patch.object(views, "_students_query") as mocked:
            yield mocked

    @pytest.fixture
    def get_page(self, patch):
        return patch("lms.views.dashboard.api.user.get_page")
