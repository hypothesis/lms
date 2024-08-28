from unittest.mock import sentinel

import pytest
from h_matchers import Any
from sqlalchemy import select

from lms.models import CourseRoster
from lms.services.course_roster import CourseRosterService, factory
from tests import factories


class TestLTINameRolesServices:
    def test_fetch_roster(
        self,
        svc,
        lti_names_roles_service,
        lti_v13_application_instance,
        db_session,
        names_and_roles_roster_response,
        lti_role_service,
    ):
        lms_course = factories.LMSCourse(lti_context_memberships_url="SERVICE_URL")
        factories.LMSCourseApplicationInstance(
            lms_course=lms_course, application_instance=lti_v13_application_instance
        )
        # Active user not returned by the roster, should be marked inactive
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

        svc.fetch_roster(lms_course)

        lti_names_roles_service.get_context_memberships.assert_called_once_with(
            lti_v13_application_instance.lti_registration, "SERVICE_URL"
        )
        lti_role_service.get_roles.assert_called_once_with(
            Any.list.containing(["ROLE2", "ROLE1"])
        )

        course_roster = db_session.scalars(
            select(CourseRoster)
            .where(CourseRoster.lms_course_id == lms_course.id)
            .order_by(CourseRoster.lms_user_id)
        ).all()

        assert len(course_roster) == 4
        assert course_roster[0].lms_course_id == lms_course.id
        assert course_roster[0].lms_user.lti_user_id == "EXISTING USER"
        assert not course_roster[0].active

        assert course_roster[1].lms_course_id == lms_course.id
        assert course_roster[1].lms_user.lti_user_id == "USER_ID"
        assert course_roster[1].active

        assert course_roster[2].lms_course_id == lms_course.id
        assert course_roster[2].lms_user.lti_user_id == "USER_ID"
        assert course_roster[2].active

        assert course_roster[3].lms_course_id == lms_course.id
        assert course_roster[3].lms_user.lti_user_id == "USER_ID_INACTIVE"
        assert not course_roster[3].active

    @pytest.fixture
    def names_and_roles_roster_response(self):
        return [
            {"user_id": "USER_ID", "roles": ["ROLE1", "ROLE2"], "status": "Active"},
            {"user_id": "USER_ID_INACTIVE", "roles": ["ROLE1"], "status": "Inactive"},
        ]

    @pytest.fixture
    def svc(self, lti_names_roles_service, lti_role_service, db_session):
        return CourseRosterService(
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
        CourseRosterService,
        lti_names_roles_service,
        lti_role_service,
    ):
        service = factory(sentinel.context, pyramid_request)

        CourseRosterService.assert_called_once_with(
            db=db_session,
            lti_names_roles_service=lti_names_roles_service,
            lti_role_service=lti_role_service,
            h_authority=pyramid_request.registry.settings["h_authority"],
        )
        assert service == CourseRosterService.return_value

    @pytest.fixture
    def CourseRosterService(self, patch):
        return patch("lms.services.course_roster.CourseRosterService")
