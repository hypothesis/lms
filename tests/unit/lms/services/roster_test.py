from datetime import datetime
from unittest.mock import Mock, sentinel

import pytest
from h_matchers import Any
from sqlalchemy import select

from lms.models import AssignmentRoster, CourseRoster, LMSSegmentRoster
from lms.services.exceptions import ExternalRequestError
from lms.services.roster import RosterService, factory
from tests import factories


class TestRosterService:
    @pytest.mark.parametrize(
        "create_roster,expected",
        [(True, datetime(2021, 1, 1)), (False, None)],
    )
    def test_assignment_roster_last_updated(
        self, svc, assignment, db_session, create_roster, expected
    ):
        lms_user = factories.LMSUser()
        lti_role = factories.LTIRole()

        if create_roster:
            factories.AssignmentRoster(
                updated=datetime(2021, 1, 1),
                lms_user=lms_user,
                assignment=assignment,
                lti_role=lti_role,
                active=True,
            )
        db_session.flush()

        assert svc.assignment_roster_last_updated(assignment) == expected

    @pytest.mark.parametrize(
        "create_roster,expected",
        [(True, datetime(2021, 1, 1)), (False, None)],
    )
    def test_course_roster_last_updated(
        self, svc, lms_course, db_session, create_roster, expected
    ):
        lms_user = factories.LMSUser()
        lti_role = factories.LTIRole()

        if create_roster:
            factories.CourseRoster(
                updated=datetime(2021, 1, 1),
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
        lti_role_service.get_roles.assert_called_once_with(
            Any.list.containing(["ROLE2", "ROLE1"])
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
        lti_role_service.get_roles.assert_called_once_with(
            Any.list.containing(["ROLE2", "ROLE1"])
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

    def test_fetch_assignment_roster_with_canvas_user_id(
        self, svc, lti_names_roles_service, db_session, lti_role_service, assignment
    ):
        lti_names_roles_service.get_context_memberships.return_value = [
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
        ]
        lti_role_service.get_roles.return_value = [
            factories.LTIRole(value="ROLE1"),
        ]

        svc.fetch_assignment_roster(assignment)

        roster = db_session.scalars(
            select(AssignmentRoster)
            .order_by(AssignmentRoster.lms_user_id)
            .where(AssignmentRoster.assignment_id == assignment.id)
        ).all()

        assert roster[0].assignment_id == assignment.id
        assert roster[0].lms_user.lti_user_id == "USER_ID"
        assert roster[0].lms_user.lms_api_user_id == "API_ID"

    @pytest.mark.parametrize(
        "known_error",
        [
            "Requested ResourceLink bound to unexpected external tool",
            "Requested ResourceLink was not found",
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
        lti_role_service.get_roles.assert_called_once_with(
            Any.list.containing(["ROLE2", "ROLE1"])
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

    @pytest.fixture
    def lms_course(self, lti_v13_application_instance):
        lms_course = factories.LMSCourse(lti_context_memberships_url="SERVICE_URL")
        factories.LMSCourseApplicationInstance(
            lms_course=lms_course, application_instance=lti_v13_application_instance
        )

        return lms_course

    @pytest.fixture
    def assignment(self, lms_course):
        course = factories.Course(
            authority_provided_id=lms_course.h_authority_provided_id
        )
        return factories.Assignment(lti_v13_resource_link_id="LTI1.3_ID", course=course)

    @pytest.fixture
    def names_and_roles_roster_response(self):
        return [
            {"user_id": "USER_ID", "roles": ["ROLE1", "ROLE2"], "status": "Active"},
            {"user_id": "USER_ID_INACTIVE", "roles": ["ROLE1"], "status": "Inactive"},
        ]

    @pytest.fixture
    def svc(self, lti_names_roles_service, lti_role_service, db_session):
        return RosterService(
            db_session,
            lti_names_roles_service=lti_names_roles_service,
            lti_role_service=lti_role_service,
            h_authority="AUTHORITY",
        )


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        db_session,
        RosterService,
        lti_names_roles_service,
        lti_role_service,
    ):
        service = factory(sentinel.context, pyramid_request)

        RosterService.assert_called_once_with(
            db=db_session,
            lti_names_roles_service=lti_names_roles_service,
            lti_role_service=lti_role_service,
            h_authority=pyramid_request.registry.settings["h_authority"],
        )
        assert service == RosterService.return_value

    @pytest.fixture
    def RosterService(self, patch):
        return patch("lms.services.roster.RosterService")
