from unittest.mock import sentinel

import pytest

from lms.services.course_roster import CourseRosterService, factory
from tests import factories


class TestLTINameRolesServices:
    def test_fetch_roster(
        self, svc, lti_names_roles_service, lti_v13_application_instance, db_session
    ):
        lms_course = factories.LMSCourse(lti_context_memberships_url="SERVICE_URL")
        factories.LMSCourseApplicationInstance(
            lms_course=lms_course, application_instance=lti_v13_application_instance
        )
        db_session.flush()

        svc.fetch_roster(lms_course)

        lti_names_roles_service.get_context_memberships.assert_called_once_with(
            lti_v13_application_instance.lti_registration, "SERVICE_URL"
        )

    @pytest.fixture
    def svc(self, lti_names_roles_service, db_session):
        return CourseRosterService(
            db_session, lti_names_roles_service=lti_names_roles_service
        )


class TestFactory:
    def test_it(
        self, pyramid_request, db_session, CourseRosterService, lti_names_roles_service
    ):
        service = factory(sentinel.context, pyramid_request)

        CourseRosterService.assert_called_once_with(
            db=db_session, lti_names_roles_service=lti_names_roles_service
        )
        assert service == CourseRosterService.return_value

    @pytest.fixture
    def CourseRosterService(self, patch):
        return patch("lms.services.course_roster.CourseRosterService")
