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
            # Not a checkpointed assignment: no phases to bucket by.
            document_uri=None,
            due_date=None,
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
                        "replies": 3,
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

    def test_students_metrics_sums_the_phases_of_a_checkpointed_assignment(
        self,
        views,
        pyramid_request,
        h_api,
        student,
        dashboard_service,
        assignment_service,
        auto_grading_service,
        db_session,
    ):
        pyramid_request.parsed_params = {
            "h_userids": sentinel.h_userids,
            "assignment_id": sentinel.assignment_id,
        }
        first_config, second_config = factories.AutoGradingConfig.create_batch(2)
        assignment = factories.Assignment(
            course=factories.Course(),
            checkpoint_enabled=True,
            document_uri="https://example.com/reading",
            due_date=datetime(2024, 2, 1),  # noqa: DTZ001
            # Points at the head of the chain, which is what gates the
            # per-phase grades.
            auto_grading_config=first_config,
        )
        db_session.flush()
        dashboard_service.get_request_assignment.return_value = assignment
        dashboard_service.get_assignment_roster.return_value = (
            None,
            select(User).where(User.id == student.id).add_columns(True),  # noqa: FBT003
        )
        assignment_service.get_auto_grading_configs.return_value = [
            first_config,
            second_config,
        ]
        # One row per phase, which is what group_by "user_phase" returns.
        h_api.get_annotation_counts.return_value = [
            {
                "display_name": student.display_name,
                "userid": student.h_userid,
                "phase": 1,
                "ends_at": "2024-01-15",
                "annotations": 2,
                "page_notes": 1,
                "replies": 4,
                "last_activity": "2024-01-10",
            },
            {
                "display_name": student.display_name,
                "userid": student.h_userid,
                "phase": 2,
                "ends_at": None,
                "annotations": 3,
                "page_notes": 0,
                "replies": 1,
                "last_activity": "2024-01-20",
            },
        ]

        response = views.students_metrics()

        h_api.get_annotation_counts.assert_called_once_with(
            [g.authority_provided_id for g in assignment.groupings],
            group_by="user_phase",
            resource_link_ids=[assignment.resource_link_id],
            h_userids=sentinel.h_userids,
            document_uri="https://example.com/reading",
            due_date=assignment.due_date,
        )

        (api_student,) = response["students"]
        # The overall figures are the phases added up: annotations fold in page
        # notes (2+1 and 3+0), replies are 4+1, and the last activity is the
        # latest of the two.
        assert api_student["annotation_metrics"] == {
            "annotations": 6,
            "replies": 5,
            "last_activity": datetime(2024, 1, 20),  # noqa: DTZ001
        }
        assert api_student["phase_metrics"] == [
            {
                "phase": 1,
                "ends_at": datetime(2024, 1, 15),  # noqa: DTZ001
                "started": True,
                "metrics": {
                    "annotations": 3,
                    "replies": 4,
                    "last_activity": datetime(2024, 1, 10),  # noqa: DTZ001
                },
                "grade": auto_grading_service.calculate_grade.return_value,
                "requirements": first_config.asdict(),
            },
            {
                "phase": 2,
                # The checkpoint hasn't been revealed, or there's no due date:
                # either way this phase hasn't closed.
                "ends_at": None,
                # Phase 1 closed, so this one is open.
                "started": True,
                "metrics": {
                    "annotations": 3,
                    "replies": 1,
                    "last_activity": datetime(2024, 1, 20),  # noqa: DTZ001
                },
                "grade": auto_grading_service.calculate_grade.return_value,
                "requirements": second_config.asdict(),
            },
        ]
        # Each phase is graded against the config at its own position, not the
        # same one twice.
        auto_grading_service.calculate_grade.assert_has_calls(
            [
                call(first_config, api_student["phase_metrics"][0]["metrics"]),
                call(second_config, api_student["phase_metrics"][1]["metrics"]),
            ]
        )

    @pytest.mark.parametrize(
        ("first_phase_ends_at", "expected"),
        [
            # Phase 1 closed, so phase 2 has started and both count.
            ("2024-01-15", 0.375),
            # Phase 1 is still open, so phase 2 hasn't started.
            (None, 0.25),
            # A scheduled reveal that hasn't fired yet closes nothing.
            ("2099-01-01", 0.25),
        ],
    )
    def test_students_metrics_averages_the_started_phases(
        self,
        views,
        pyramid_request,
        h_api,
        student,
        dashboard_service,
        assignment_service,
        auto_grading_service,
        db_session,
        first_phase_ends_at,
        expected,
    ):
        pyramid_request.parsed_params = {
            "h_userids": sentinel.h_userids,
            "assignment_id": sentinel.assignment_id,
        }
        first_config, second_config = factories.AutoGradingConfig.create_batch(2)
        assignment = factories.Assignment(
            course=factories.Course(),
            checkpoint_enabled=True,
            document_uri="https://example.com/reading",
            auto_grading_config=first_config,
        )
        db_session.flush()
        dashboard_service.get_request_assignment.return_value = assignment
        dashboard_service.get_assignment_roster.return_value = (
            None,
            select(User).where(User.id == student.id).add_columns(True),  # noqa: FBT003
        )
        assignment_service.get_auto_grading_configs.return_value = [
            first_config,
            second_config,
        ]
        auto_grading_service.get_last_grades.return_value = {}
        auto_grading_service.calculate_grade.side_effect = [0.25, 0.5]
        h_api.get_annotation_counts.return_value = [
            {
                "display_name": student.display_name,
                "userid": student.h_userid,
                "phase": phase,
                "ends_at": ends_at,
                "annotations": 1,
                "page_notes": 0,
                "replies": 0,
                "last_activity": "2024-01-10",
            }
            for phase, ends_at in ((1, first_phase_ends_at), (2, None))
        ]

        response = views.students_metrics()

        (api_student,) = response["students"]
        assert api_student["auto_grading_grade"]["current_grade"] == expected
        # Each phase carries what it was graded against, so the dashboard can
        # show how the average was reached.
        assert [phase["requirements"] for phase in api_student["phase_metrics"]] == [
            first_config.asdict(),
            second_config.asdict(),
        ]

    def test_students_metrics_zero_fills_the_phases_h_reports_nothing_for(
        self,
        views,
        pyramid_request,
        h_api,
        student,
        dashboard_service,
        assignment_service,
        db_session,
    ):
        pyramid_request.parsed_params = {
            "h_userids": sentinel.h_userids,
            "assignment_id": sentinel.assignment_id,
        }
        assignment = factories.Assignment(
            course=factories.Course(),
            checkpoint_enabled=True,
            document_uri="https://example.com/reading",
        )
        db_session.flush()
        dashboard_service.get_request_assignment.return_value = assignment
        dashboard_service.get_assignment_roster.return_value = (
            None,
            select(User).where(User.id == student.id).add_columns(True),  # noqa: FBT003
        )
        # No configs, so the phase count can only come from h.
        assignment_service.get_auto_grading_configs.return_value = []
        h_api.get_annotation_counts.return_value = [
            {
                "display_name": None,
                "userid": None,
                "phase": phase,
                "ends_at": None,
                "annotations": 7,
                "page_notes": 0,
                "replies": 2,
                "last_activity": "2024-01-10",
            }
            for phase in (1, 2)
        ]

        response = views.students_metrics()

        (api_student,) = response["students"]
        # One zeroed entry per phase h reported.
        assert api_student["phase_metrics"] == [
            {
                "phase": 1,
                "ends_at": None,
                "started": True,
                "metrics": {
                    "annotations": 0,
                    "replies": 0,
                    "last_activity": None,
                },
            },
            {
                "phase": 2,
                "ends_at": None,
                # Nothing has closed phase 1, so this one hasn't begun: the
                # dashboard shows it blank rather than as a zero.
                "started": False,
                "metrics": {
                    "annotations": 0,
                    "replies": 0,
                    "last_activity": None,
                },
            },
        ]

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
            # Not a checkpointed assignment: no phases to bucket by.
            document_uri=None,
            due_date=None,
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
                        "replies": 3,
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
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
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
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
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
                "replies": 3,
                "userid": student.h_userid,
                "last_activity": "2024-01-01",
            },
            {
                "display_name": sentinel.display_name,
                "annotations": 5,
                "page_notes": 5,
                "replies": 7,
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
