from unittest.mock import patch, sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized

from lms.models import DashboardAdmin, RoleScope, RoleType
from lms.services.dashboard import DashboardService, factory
from tests import factories

pytestmark = pytest.mark.usefixtures("h_api", "assignment_service")


class TestDashboardService:
    def test_get_request_assignment_404(self, pyramid_request, assignment_service, svc):
        assignment_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            svc.get_request_assignment(pyramid_request, sentinel.id)

    def test_get_request_assignment_403(self, pyramid_request, course_service, svc):
        course_service.is_member.return_value = False

        with pytest.raises(HTTPUnauthorized):
            svc.get_request_assignment(pyramid_request, sentinel.id)

    def test_get_request_assignment_for_staff(
        self, pyramid_request, assignment_service, pyramid_config, svc
    ):
        pyramid_config.testing_securitypolicy(permissive=True)
        assignment_service.is_member.return_value = False

        assert svc.get_request_assignment(pyramid_request, sentinel.id)

    def test_get_request_assignment(
        self, pyramid_request, course_service, svc, assignment_service
    ):
        course_service.is_member.return_value = True

        assert svc.get_request_assignment(pyramid_request, sentinel.id)

        course_service.is_member.assert_called_once_with(
            assignment_service.get_by_id.return_value.course,
            pyramid_request.user.h_userid,
        )

    def test_get_request_assignment_for_admin(
        self,
        pyramid_request,
        assignment_service,
        svc,
        organization,
        db_session,
        course,
        get_request_admin_organizations,
    ):
        assignment = factories.Assignment(course_id=course.id)
        db_session.flush()
        assignment_service.get_by_id.return_value = assignment
        get_request_admin_organizations.return_value = [organization]

        assert svc.get_request_assignment(pyramid_request, sentinel.id)

    def test_get_request_course_404(
        self,
        pyramid_request,
        course_service,
        svc,
    ):
        course_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            svc.get_request_course(pyramid_request, sentinel.id)

    def test_get_request_course_403(self, pyramid_request, course_service, svc):
        course_service.is_member.return_value = False

        with pytest.raises(HTTPUnauthorized):
            svc.get_request_course(pyramid_request, sentinel.id)

    def test_get_request_course_for_staff(
        self, pyramid_request, course_service, pyramid_config, svc
    ):
        pyramid_config.testing_securitypolicy(permissive=True)
        course_service.is_member.return_value = False

        assert svc.get_request_course(pyramid_request, sentinel.id)

    def test_get_request_course_for_admin(
        self,
        pyramid_request,
        course_service,
        svc,
        organization,
        get_request_admin_organizations,
        course,
    ):
        course_service.get_by_id.return_value = course
        get_request_admin_organizations.return_value = [organization]

        assert svc.get_request_course(pyramid_request, sentinel.id)

    def test_get_request_course(self, pyramid_request, course_service, svc):
        course_service.is_member.return_value = True

        assert svc.get_request_course(pyramid_request, sentinel.id)

    def test_add_dashboard_admin(self, svc, db_session):
        admin = svc.add_dashboard_admin(
            factories.Organization(), "testing@example.com", "creator"
        )

        assert db_session.query(DashboardAdmin).one() == admin

    def test_delete_dashboard_admin(self, svc, db_session, organization):
        admin = factories.DashboardAdmin(
            organization=organization, email="testing@example.com", created_by="creator"
        )
        db_session.flush()

        svc.delete_dashboard_admin(admin.id)

        assert not db_session.query(DashboardAdmin).filter_by(id=admin.id).first()

    def test_get_organizations_where_admin(
        self, svc, db_session, organization, organization_service
    ):
        # Admin user
        lms_admin = factories.LMSUser(h_userid="admin")

        # Organization where just a teacher
        organization_lti_teacher = factories.Organization()
        teacher_course = factories.LMSCourse()
        ai = factories.ApplicationInstance(organization=organization_lti_teacher)
        factories.LMSCourseApplicationInstance(
            lms_course=teacher_course, application_instance=ai
        )
        factories.LMSCourseMembership(
            lms_course=teacher_course,
            lms_user=lms_admin,
            lti_role=factories.LTIRole(
                type=RoleType.INSTRUCTOR, scope=RoleScope.COURSE
            ),
        )

        # Organization where admin via an LTIRole
        organization_lti_admin = factories.Organization(parent=organization_lti_teacher)
        course = factories.LMSCourse()
        ai = factories.ApplicationInstance(organization=organization_lti_admin)
        factories.LMSCourseApplicationInstance(
            lms_course=course, application_instance=ai
        )
        factories.LMSCourseMembership(
            lms_course=course,
            lms_user=lms_admin,
            lti_role=factories.LTIRole(type=RoleType.ADMIN, scope=RoleScope.SYSTEM),
        )
        # Organization where admin via email
        child_organization = factories.Organization(parent=organization)
        email_admin = factories.DashboardAdmin(
            organization=organization, email="testing@example.com", created_by="creator"
        )
        db_session.flush()
        organization_service.get_hierarchy_ids.side_effect = (
            [
                organization.id,
                child_organization.id,
            ],
            [organization_lti_admin.id],
        )

        assert set(
            svc.get_organizations_where_admin(lms_admin.h_userid, email_admin.email)
        ) == {organization, child_organization, organization_lti_admin}

    def test_get_request_admin_organizations_for_non_staff(self, pyramid_request, svc):
        pyramid_request.params = {"org_public_id": sentinel.public_id}

        assert not svc.get_request_admin_organizations(pyramid_request)

    def test_get_request_admin_organizations_no_parameter(
        self, pyramid_request, svc, pyramid_config
    ):
        pyramid_config.testing_securitypolicy(permissive=True)

        assert not svc.get_request_admin_organizations(pyramid_request)

    def test_get_request_admin_organizations_no_organization(
        self, pyramid_request, svc, pyramid_config, organization_service
    ):
        pyramid_config.testing_securitypolicy(permissive=True)
        organization_service.get_by_public_id.return_value = None
        pyramid_request.params = {"org_public_id": sentinel.public_id}

        with pytest.raises(HTTPNotFound):
            svc.get_request_admin_organizations(pyramid_request)

    def test_get_request_admin_organizations(
        self, pyramid_request, svc, pyramid_config, organization_service, organization
    ):
        pyramid_config.testing_securitypolicy(permissive=True)
        organization_service.get_by_public_id.return_value = organization
        organization_service.get_hierarchy_ids.return_value = [organization.id]
        pyramid_request.params = {"org_public_id": sentinel.public_id}

        assert svc.get_request_admin_organizations(pyramid_request) == [organization]
        organization_service.get_by_public_id.assert_called_once_with(
            sentinel.public_id
        )

    def test_get_request_admin_organizations_for_staff(
        self, svc, pyramid_config, pyramid_request, organization, organization_service
    ):
        pyramid_config.testing_securitypolicy(permissive=True)
        pyramid_request.params = {"org_public_id": sentinel.id}
        organization_service.get_by_public_id.return_value = organization
        organization_service.get_hierarchy_ids.return_value = [organization.id]

        assert svc.get_request_admin_organizations(pyramid_request) == [organization]

    @pytest.fixture()
    def svc(
        self, assignment_service, course_service, organization_service, pyramid_request
    ):
        return DashboardService(
            pyramid_request,
            assignment_service,
            course_service,
            organization_service,
            "authority",
        )

    @pytest.fixture(autouse=True)
    def organization_service(self, organization_service, organization):
        organization_service.get_by_public_id.return_value = organization
        organization_service.get_hierarchy_ids.return_value = []
        return organization_service

    @pytest.fixture()
    def course(self, db_session, application_instance):
        course = factories.Course(application_instance=application_instance)
        db_session.flush()
        return course

    @pytest.fixture()
    def get_request_admin_organizations(self, svc):
        with patch.object(
            svc, "get_request_admin_organizations"
        ) as get_request_admin_organizations:
            yield get_request_admin_organizations

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config):
        pyramid_config.testing_securitypolicy(permissive=False)
        return pyramid_config


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        assignment_service,
        DashboardService,
        course_service,
        organization_service,
    ):
        service = factory(sentinel.context, pyramid_request)

        DashboardService.assert_called_once_with(
            request=pyramid_request,
            assignment_service=assignment_service,
            course_service=course_service,
            organization_service=organization_service,
            h_authority="lms.hypothes.is",
        )
        assert service == DashboardService.return_value

    @pytest.fixture
    def DashboardService(self, patch):
        return patch("lms.services.dashboard.DashboardService")
