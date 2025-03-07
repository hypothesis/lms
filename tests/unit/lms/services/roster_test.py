import logging
from datetime import datetime
from unittest.mock import Mock, call, sentinel

import pytest
from h_matchers import Any
from sqlalchemy import select

from lms.models import AssignmentRoster, CourseRoster, LMSSegmentRoster
from lms.models.family import Family
from lms.models.lms_segment import LMSSegment
from lms.models.lms_user import LMSUser
from lms.models.lti_role import RoleScope, RoleType
from lms.services.exceptions import (
    CanvasAPIError,
    ConcurrentTokenRefreshError,
    ExternalRequestError,
    OAuth2TokenError,
)
from lms.services.roster import RosterService, factory
from tests import factories


class TestRosterService:
    @pytest.mark.parametrize(
        "create_roster,expected",
        [(True, datetime(2021, 1, 1)), (False, None)],  # noqa: DTZ001
    )
    def test_assignment_roster_last_updated(
        self, svc, assignment, db_session, create_roster, expected
    ):
        lms_user = factories.LMSUser()
        lti_role = factories.LTIRole()

        if create_roster:
            factories.AssignmentRoster(
                updated=datetime(2021, 1, 1),  # noqa: DTZ001
                lms_user=lms_user,
                assignment=assignment,
                lti_role=lti_role,
                active=True,
            )
        db_session.flush()

        assert svc.assignment_roster_last_updated(assignment) == expected

    @pytest.mark.parametrize(
        "create_roster,expected",
        [(True, datetime(2021, 1, 1)), (False, None)],  # noqa: DTZ001
    )
    def test_segment_roster_last_updated(
        self, svc, lms_segment, db_session, create_roster, expected
    ):
        lms_user = factories.LMSUser()
        lti_role = factories.LTIRole()

        if create_roster:
            factories.LMSSegmentRoster(
                updated=datetime(2021, 1, 1),  # noqa: DTZ001
                lms_user=lms_user,
                lms_segment=lms_segment,
                lti_role=lti_role,
                active=True,
            )
        db_session.flush()

        assert svc.segment_roster_last_updated(lms_segment) == expected

    @pytest.mark.parametrize(
        "create_roster,expected",
        [(True, datetime(2021, 1, 1)), (False, None)],  # noqa: DTZ001
    )
    def test_course_roster_last_updated(
        self, svc, lms_course, db_session, create_roster, expected
    ):
        lms_user = factories.LMSUser()
        lti_role = factories.LTIRole()

        if create_roster:
            factories.CourseRoster(
                updated=datetime(2021, 1, 1),  # noqa: DTZ001
                lms_user=lms_user,
                lms_course=lms_course,
                lti_role=lti_role,
                active=True,
            )
        db_session.flush()

        assert svc.course_roster_last_updated(lms_course) == expected

    @pytest.mark.parametrize("with_role_scope", [True, False])
    @pytest.mark.parametrize("with_role_type", [True, False])
    @pytest.mark.parametrize("with_h_userids", [True, False])
    def test_get_course_roster(
        self,
        svc,
        lms_course,
        db_session,
        with_role_scope,
        with_role_type,
        with_h_userids,
    ):
        lms_user = factories.LMSUser()
        inactive_lms_user = factories.LMSUser()
        lti_role = factories.LTIRole()

        factories.CourseRoster(
            lms_user=lms_user,
            lms_course=lms_course,
            lti_role=lti_role,
            active=True,
        )
        factories.CourseRoster(
            lms_user=inactive_lms_user,
            lms_course=lms_course,
            lti_role=lti_role,
            active=False,
        )
        db_session.flush()

        result = db_session.execute(
            svc.get_course_roster(
                lms_course,
                role_scope=lti_role.scope if with_role_scope else None,
                role_type=lti_role.type if with_role_type else None,
                h_userids=[lms_user.h_userid, inactive_lms_user.h_userid]
                if with_h_userids
                else None,
            )
        ).all()

        assert [(lms_user, True), (inactive_lms_user, False)] == result

    @pytest.mark.parametrize("with_role_scope", [True, False])
    @pytest.mark.parametrize("with_role_type", [True, False])
    @pytest.mark.parametrize("with_h_userids", [True, False])
    def test_get_assignment_roster(
        self,
        svc,
        assignment,
        db_session,
        with_role_type,
        with_role_scope,
        with_h_userids,
    ):
        lms_user = factories.LMSUser()
        inactive_lms_user = factories.LMSUser()
        lti_role = factories.LTIRole()

        factories.AssignmentRoster(
            lms_user=lms_user,
            assignment=assignment,
            lti_role=lti_role,
            active=True,
        )
        factories.AssignmentRoster(
            lms_user=inactive_lms_user,
            assignment=assignment,
            lti_role=lti_role,
            active=False,
        )
        db_session.flush()

        result = db_session.execute(
            svc.get_assignment_roster(
                assignment,
                role_scope=lti_role.scope if with_role_scope else None,
                role_type=lti_role.type if with_role_type else None,
                h_userids=[lms_user.h_userid, inactive_lms_user.h_userid]
                if with_h_userids
                else None,
            )
        ).all()

        assert [(lms_user, True), (inactive_lms_user, False)] == result

    @pytest.mark.parametrize("with_role_scope", [True, False])
    @pytest.mark.parametrize("with_role_type", [True, False])
    @pytest.mark.parametrize("with_h_userids", [True, False])
    def test_get_segment_roster(
        self,
        svc,
        lms_segment,
        db_session,
        with_role_type,
        with_role_scope,
        with_h_userids,
    ):
        lms_user = factories.LMSUser()
        inactive_lms_user = factories.LMSUser()
        lti_role = factories.LTIRole()

        factories.LMSSegmentRoster(
            lms_user=lms_user,
            lms_segment=lms_segment,
            lti_role=lti_role,
            active=True,
        )
        factories.LMSSegmentRoster(
            lms_user=inactive_lms_user,
            lms_segment=lms_segment,
            lti_role=lti_role,
            active=False,
        )
        db_session.flush()

        result = db_session.execute(
            svc.get_segments_roster(
                [lms_segment],
                role_scope=lti_role.scope if with_role_scope else None,
                role_type=lti_role.type if with_role_type else None,
                h_userids=[lms_user.h_userid, inactive_lms_user.h_userid]
                if with_h_userids
                else None,
            )
        ).all()

        assert [(lms_user, True), (inactive_lms_user, False)] == result

    def test_get_assignment_roster_doesnt_return_duplicates(
        self, assignment, db_session, svc
    ):
        lms_user = factories.LMSUser()
        lti_role_1 = factories.LTIRole()
        lti_role_2 = factories.LTIRole()

        factories.AssignmentRoster(
            lms_user=lms_user,
            assignment=assignment,
            lti_role=lti_role_1,
            active=True,
        )
        factories.AssignmentRoster(
            lms_user=lms_user,
            assignment=assignment,
            lti_role=lti_role_2,
            active=True,
        )
        db_session.flush()

        result = db_session.execute(svc.get_assignment_roster(assignment)).all()

        assert [(lms_user, True)] == result

    def test_fetch_course_roster(
        self,
        svc,
        lti_names_roles_service,
        lti_v13_application_instance,
        db_session,
        names_and_roles_roster_response,
        lti_role_service,
        lms_course,
    ):
        # Active user not returned by the roster, should be marked inactive after fetch the roster
        factories.CourseRoster(
            lms_course=lms_course,
            lms_user=factories.LMSUser(lti_user_id="EXISTING USER"),
            lti_role=factories.LTIRole(),
            active=True,
        )
        db_session.flush()
        lti_names_roles_service.get_context_memberships.return_value = (
            names_and_roles_roster_response
        )
        lti_role_service.get_roles.return_value = [
            factories.LTIRole(value="ROLE1"),
            factories.LTIRole(value="ROLE2"),
        ]

        svc.fetch_course_roster(lms_course)

        lti_names_roles_service.get_context_memberships.assert_called_once_with(
            lti_v13_application_instance.lti_registration, "SERVICE_URL"
        )
        lti_role_service.get_roles.assert_has_calls(
            [
                call(Any.list.containing(["ROLE1", "ROLE2"])),
                call(["ROLE1"]),
                call(Any.list.containing(["ROLE1", "ROLE2"])),
            ]
        )

        roster = db_session.scalars(
            select(CourseRoster)
            .where(CourseRoster.lms_course_id == lms_course.id)
            .order_by(CourseRoster.lms_user_id)
        ).all()

        assert len(roster) == 4
        assert roster[0].lms_course_id == lms_course.id
        assert roster[0].lms_user.lti_user_id == "EXISTING USER"
        assert not roster[0].active

        assert roster[1].lms_course_id == lms_course.id
        assert roster[1].lms_user.lti_user_id == "USER_ID"
        assert roster[1].active

        assert roster[2].lms_course_id == lms_course.id
        assert roster[2].lms_user.lti_user_id == "USER_ID"
        assert roster[2].active

        assert roster[3].lms_course_id == lms_course.id
        assert roster[3].lms_user.lti_user_id == "USER_ID_INACTIVE"
        assert not roster[3].active

    def test_fetch_assignment_roster(
        self,
        svc,
        lti_names_roles_service,
        lti_v13_application_instance,
        db_session,
        names_and_roles_roster_response,
        lti_role_service,
        assignment,
    ):
        # Active user not returned by the roster, should be marked inactive after fetch the roster
        factories.AssignmentRoster(
            assignment=assignment,
            lms_user=factories.LMSUser(lti_user_id="EXISTING USER"),
            lti_role=factories.LTIRole(),
            active=True,
        )
        db_session.flush()
        lti_names_roles_service.get_context_memberships.return_value = (
            names_and_roles_roster_response
        )
        lti_role_service.get_roles.return_value = [
            factories.LTIRole(value="ROLE1"),
            factories.LTIRole(value="ROLE2"),
        ]

        svc.fetch_assignment_roster(assignment)

        lti_names_roles_service.get_context_memberships.assert_called_once_with(
            lti_v13_application_instance.lti_registration, "SERVICE_URL", "LTI1.3_ID"
        )
        lti_role_service.get_roles.assert_has_calls(
            [
                call(Any.list.containing(["ROLE1", "ROLE2"])),
                call(["ROLE1"]),
                call(Any.list.containing(["ROLE1", "ROLE2"])),
            ]
        )

        roster = db_session.scalars(
            select(AssignmentRoster)
            .order_by(AssignmentRoster.lms_user_id)
            .where(AssignmentRoster.assignment_id == assignment.id)
        ).all()

        assert len(roster) == 4
        assert roster[0].assignment_id == assignment.id
        assert roster[0].lms_user.lti_user_id == "EXISTING USER"
        assert not roster[0].active

        assert roster[1].assignment_id == assignment.id
        assert roster[1].lms_user.lti_user_id == "USER_ID"
        assert roster[1].active

        assert roster[2].assignment_id == assignment.id
        assert roster[2].lms_user.lti_user_id == "USER_ID"
        assert roster[2].active

        assert roster[3].assignment_id == assignment.id
        assert roster[3].lms_user.lti_user_id == "USER_ID_INACTIVE"
        assert not roster[3].active

    @pytest.mark.parametrize("collect_student_emails", [True, False])
    @pytest.mark.parametrize("is_learner", [True, False])
    @pytest.mark.parametrize(
        "response,expected_email",
        [
            (
                {
                    "user_id": "USER_ID",
                    "roles": ["ROLE1"],
                    "status": "Active",
                    "email": "USER_ID@example.com",
                },
                "USER_ID@example.com",
            ),
            (
                {"user_id": "USER_ID", "roles": ["ROLE1"], "status": "Active"},
                None,
            ),
        ],
    )
    def test_fetch_assignment_roster_saves_email(
        self,
        svc,
        lti_names_roles_service,
        db_session,
        lti_role_service,
        assignment,
        response,
        expected_email,
        application_instance,
        collect_student_emails,
        is_learner,
    ):
        application_instance.settings.set(
            "hypothesis", "collect_student_emails", collect_student_emails
        )
        lti_names_roles_service.get_context_memberships.return_value = [response]
        lti_role_service.get_roles.return_value = [
            factories.LTIRole(
                value="ROLE1",
                scope=RoleScope.COURSE,
                type=RoleType.LEARNER if is_learner else RoleType.INSTRUCTOR,
            ),
        ]

        svc.fetch_assignment_roster(assignment)

        roster = db_session.scalars(
            select(AssignmentRoster)
            .order_by(AssignmentRoster.lms_user_id)
            .where(AssignmentRoster.assignment_id == assignment.id)
        ).all()

        if (is_learner and collect_student_emails) or not is_learner:
            assert roster[0].lms_user.email == expected_email
        else:
            assert not roster[0].lms_user.email

    @pytest.mark.parametrize(
        "family,response,lms_api_user_id",
        [
            (
                None,
                {
                    "user_id": "USER_ID",
                    "roles": ["ROLE1"],
                    "status": "Active",
                },
                None,
            ),
            (
                Family.D2L.value,
                {"user_id": "USER_ID_API", "roles": ["ROLE1"], "status": "Active"},
                "API",
            ),
            (
                Family.CANVAS.value,
                {
                    "user_id": "USER_ID",
                    "roles": ["ROLE1"],
                    "status": "Active",
                    "message": [
                        {
                            "https://purl.imsglobal.org/spec/lti/claim/custom": {
                                "canvas_user_id": "API_ID"
                            }
                        }
                    ],
                },
                "API_ID",
            ),
        ],
    )
    def test_fetch_assignment_roster_with_lms_api_user_id(
        self,
        svc,
        lti_names_roles_service,
        db_session,
        lti_role_service,
        assignment,
        family,
        response,
        lms_api_user_id,
        application_instance,
    ):
        application_instance.tool_consumer_info_product_family_code = family
        lti_names_roles_service.get_context_memberships.return_value = [response]
        lti_role_service.get_roles.return_value = [
            factories.LTIRole(value="ROLE1"),
        ]

        svc.fetch_assignment_roster(assignment)

        roster = db_session.scalars(
            select(AssignmentRoster)
            .order_by(AssignmentRoster.lms_user_id)
            .where(AssignmentRoster.assignment_id == assignment.id)
        ).all()

        assert roster[0].lms_user.lms_api_user_id == lms_api_user_id

    @pytest.mark.parametrize(
        "known_error",
        [
            "Requested ResourceLink bound to unexpected external tool",
            "Requested ResourceLink was not found",
            "Requested assignment not configured for external tool launches",
            "Tool does not have access to rlid or rlid does not exist",
        ],
    )
    def test_fetch_assignment_roster_retries_with_lti_v11_id(
        self, svc, lti_names_roles_service, assignment, known_error
    ):
        lti_names_roles_service.get_context_memberships.side_effect = (
            ExternalRequestError(response=Mock(text=known_error))
        )

        # Method finishes without re-raising the exception
        assert not svc.fetch_assignment_roster(assignment)

    def test_fetch_assignment_roster_raises_external_request_error(
        self, svc, lti_names_roles_service, assignment
    ):
        lti_names_roles_service.get_context_memberships.side_effect = (
            ExternalRequestError()
        )

        with pytest.raises(ExternalRequestError):
            svc.fetch_assignment_roster(assignment)

    def test_fetch_canvas_group_roster(
        self,
        svc,
        lti_names_roles_service,
        lti_v13_application_instance,
        db_session,
        names_and_roles_roster_response,
        lti_role_service,
        lms_course,
    ):
        canvas_group = factories.LMSSegment(type="canvas_group", lms_course=lms_course)
        # Active user not returned by the roster, should be marked inactive after fetch the roster
        factories.LMSSegmentRoster(
            lms_segment=canvas_group,
            lms_user=factories.LMSUser(lti_user_id="EXISTING USER"),
            lti_role=factories.LTIRole(),
            active=True,
        )
        db_session.flush()
        lti_names_roles_service.get_context_memberships.return_value = (
            names_and_roles_roster_response
        )
        lti_role_service.get_roles.return_value = [
            factories.LTIRole(value="ROLE1"),
            factories.LTIRole(value="ROLE2"),
        ]

        svc.fetch_canvas_group_roster(canvas_group)

        lti_names_roles_service.get_context_memberships.assert_called_once_with(
            lti_v13_application_instance.lti_registration,
            f"https://{lti_v13_application_instance.lms_host()}/api/lti/groups/{canvas_group.lms_id}/names_and_roles",
        )
        lti_role_service.get_roles.assert_has_calls(
            [
                call(Any.list.containing(["ROLE1", "ROLE2"])),
                call(["ROLE1"]),
                call(Any.list.containing(["ROLE1", "ROLE2"])),
            ]
        )

        roster = db_session.scalars(
            select(LMSSegmentRoster)
            .order_by(LMSSegmentRoster.lms_user_id)
            .where(LMSSegmentRoster.lms_segment_id == canvas_group.id)
        ).all()

        assert len(roster) == 4
        assert roster[0].lms_segment_id == canvas_group.id
        assert roster[0].lms_user.lti_user_id == "EXISTING USER"
        assert not roster[0].active

        assert roster[1].lms_segment_id == canvas_group.id
        assert roster[1].lms_user.lti_user_id == "USER_ID"
        assert roster[1].active

        assert roster[2].lms_segment_id == canvas_group.id
        assert roster[2].lms_user.lti_user_id == "USER_ID"
        assert roster[2].active

        assert roster[3].lms_segment_id == canvas_group.id
        assert roster[3].lms_user.lti_user_id == "USER_ID_INACTIVE"
        assert not roster[3].active

    @pytest.mark.usefixtures("canvas_section")
    def test_fetch_canvas_sections_roster_with_no_instructor_token(
        self, svc, lms_course, caplog
    ):
        svc.fetch_canvas_sections_roster(lms_course)

        assert "No instructor found" in caplog.records[0].message

    @pytest.mark.usefixtures("instructor_in_course")
    def test_fetch_canvas_sections_roster_with_no_db_sections(
        self, svc, lms_course, caplog
    ):
        svc.fetch_canvas_sections_roster(lms_course)

        assert "No sections found in the DB" in caplog.records[0].message

    @pytest.mark.usefixtures("instructor_in_course", "canvas_section")
    def test_fetch_canvas_sections_roster_with_no_api_sections(
        self, svc, lms_course, caplog, canvas_api_client
    ):
        canvas_api_client.course_sections.return_value = []

        svc.fetch_canvas_sections_roster(lms_course)

        assert "No sections found on the API" in caplog.records[0].message

    @pytest.mark.usefixtures("instructor_in_course")
    @pytest.mark.parametrize("students", [None, []])
    def test_fetch_canvas_sections_roster_with_nothing_to_insert(
        self, svc, lms_course, caplog, canvas_api_client, students, canvas_section
    ):
        canvas_api_client.course_sections.return_value = [
            {"id": canvas_section.id, "name": "Section 1", "students": students}
        ]

        svc.fetch_canvas_sections_roster(lms_course)

        assert "No roster entries" in caplog.records[0].message

    def test_fetch_canvas_sections_roster(
        self,
        svc,
        lms_course,
        student_in_course,
        canvas_api_client,
        canvas_section,
        canvas_api_client_factory,
        db_session,
        pyramid_request,
        lti_v13_application_instance,
        instructor_in_course,
    ):
        canvas_api_client.course_sections.return_value = [
            {
                "id": int(canvas_section.lms_id),
                "name": "Section 1",
                "students": [
                    # Student that matches student_in_course, the student in the DB
                    {"id": student_in_course.lms_api_user_id},
                    # Duplicate student, should be ignored
                    {"id": student_in_course.lms_api_user_id},
                    # Student that doesn't match any student in the DB
                    {"id": "SOME OTHER USER"},
                ],
            },
            # Section we haven't seen before in the DB
            {"id": "SOME OTHER SECTION"},
        ]

        svc.fetch_canvas_sections_roster(lms_course)

        canvas_api_client_factory.assert_called_once_with(
            None,
            pyramid_request,
            application_instance=lti_v13_application_instance,
            user_id=instructor_in_course.lti_user_id,
        )
        canvas_api_client.course_sections.assert_called_once_with(
            lms_course.lms_api_course_id, with_students=True
        )
        section_roster = db_session.scalars(
            select(LMSUser)
            .join(LMSSegmentRoster)
            .join(LMSSegment)
            .where(LMSSegment.id == canvas_section.id)
        ).all()
        assert section_roster == [student_in_course]

    @pytest.mark.usefixtures("instructor_in_course")
    def test_fetch_canvas_sections_roster_needing_refresh(
        self,
        svc,
        lms_course,
        student_in_course,
        canvas_api_client,
        canvas_section,
        db_session,
    ):
        canvas_api_client.course_sections.side_effect = [
            OAuth2TokenError(refreshable=True),
            [
                {
                    "id": int(canvas_section.lms_id),
                    "name": "Section 1",
                    "students": [
                        # Student that matches student_in_course, the student in the DB
                        {"id": student_in_course.lms_api_user_id},
                    ],
                }
            ],
        ]

        svc.fetch_canvas_sections_roster(lms_course)

        section_roster = db_session.scalars(
            select(LMSUser)
            .join(LMSSegmentRoster)
            .join(LMSSegment)
            .where(LMSSegment.id == canvas_section.id)
        ).all()
        assert section_roster == [student_in_course]

    @pytest.mark.usefixtures("instructor_in_course", "canvas_section")
    @pytest.mark.parametrize(
        "exception", [ConcurrentTokenRefreshError, OAuth2TokenError, CanvasAPIError]
    )
    def test_fetch_canvas_sections_roster_failed_refresh(
        self, svc, lms_course, canvas_api_client, caplog, exception
    ):
        canvas_api_client.course_sections.side_effect = OAuth2TokenError(
            refreshable=True
        )
        canvas_api_client.get_refreshed_token.side_effect = exception

        svc.fetch_canvas_sections_roster(lms_course)

        assert "error refreshing token" in caplog.records[0].message

    @pytest.mark.usefixtures("instructor_in_course", "canvas_section")
    def test_fetch_canvas_sections_roster_with_invalid_token(
        self,
        svc,
        lms_course,
        canvas_api_client,
        db_session,  # noqa: ARG002
        caplog,
    ):
        canvas_api_client.course_sections.side_effect = OAuth2TokenError(
            refreshable=False
        )
        canvas_api_client.get_refreshed_token.side_effect = CanvasAPIError

        svc.fetch_canvas_sections_roster(lms_course)

        assert "invalid API token" in caplog.records[0].message

    @pytest.fixture
    def lms_course(self, lti_v13_application_instance):
        lms_course = factories.LMSCourse(lti_context_memberships_url="SERVICE_URL")
        course = factories.Course(
            authority_provided_id=lms_course.h_authority_provided_id
        )
        lms_course.course = course

        factories.LMSCourseApplicationInstance(
            lms_course=lms_course, application_instance=lti_v13_application_instance
        )

        return lms_course

    @pytest.fixture
    def instructor_in_course(self, lms_course):
        instructor = factories.LMSUser()
        role = factories.LTIRole(type=RoleType.INSTRUCTOR, scope=RoleScope.COURSE)
        factories.LMSCourseMembership(
            lms_course=lms_course, lms_user=instructor, lti_role=role
        )
        return instructor

    @pytest.fixture
    def student_in_course(self, lms_course):
        role = factories.LTIRole(type=RoleType.LEARNER, scope=RoleScope.COURSE)
        student = factories.LMSUser()
        factories.LMSCourseMembership(
            lms_course=lms_course, lms_user=student, lti_role=role
        )
        return student

    @pytest.fixture
    def canvas_section(self, lms_course, db_session):
        section = factories.LMSSegment(
            type="canvas_section", lms_course=lms_course, lms_id="1"
        )
        db_session.flush()
        return section

    @pytest.fixture
    def caplog(self, caplog):
        caplog.set_level(logging.INFO)
        return caplog

    @pytest.fixture(autouse=True)
    def canvas_api_client_factory(self, patch):
        return patch("lms.services.roster.canvas_api_client_factory")

    @pytest.fixture
    def canvas_api_client(self, canvas_api_client_factory):
        return canvas_api_client_factory.return_value

    @pytest.fixture
    def assignment(self, lms_course):
        return factories.Assignment(
            lti_v13_resource_link_id="LTI1.3_ID", course=lms_course.course
        )

    @pytest.fixture
    def lms_segment(self, lms_course):
        return factories.LMSSegment(lms_course=lms_course)

    @pytest.fixture
    def names_and_roles_roster_response(self):
        return [
            {"user_id": "USER_ID", "roles": ["ROLE1", "ROLE2"], "status": "Active"},
            {"user_id": "USER_ID_INACTIVE", "roles": ["ROLE1"], "status": "Inactive"},
        ]

    @pytest.fixture
    def svc(self, lti_names_roles_service, lti_role_service, pyramid_request):
        return RosterService(
            request=pyramid_request,
            lti_names_roles_service=lti_names_roles_service,
            lti_role_service=lti_role_service,
            h_authority="AUTHORITY",
        )


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        RosterService,
        lti_names_roles_service,
        lti_role_service,
    ):
        service = factory(sentinel.context, pyramid_request)

        RosterService.assert_called_once_with(
            request=pyramid_request,
            lti_names_roles_service=lti_names_roles_service,
            lti_role_service=lti_role_service,
            h_authority=pyramid_request.registry.settings["h_authority"],
        )
        assert service == RosterService.return_value

    @pytest.fixture
    def RosterService(self, patch):
        return patch("lms.services.roster.RosterService")
