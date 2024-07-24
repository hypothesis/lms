from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized

from lms.models.dashboard_admin import DashboardAdmin
from lms.security import Identity
from lms.services.dashboard import DashboardService, factory
from tests import factories

pytestmark = pytest.mark.usefixtures("h_api", "assignment_service")


class TestDashboardService:
    def test_get_request_assignment_404(
        self,
        pyramid_request,
        assignment_service,
        svc,
    ):
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        assignment_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            svc.get_request_assignment(pyramid_request)

    def test_get_request_assignment_403(
        self,
        pyramid_request,
        assignment_service,
        svc,
    ):
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        assignment_service.is_member.return_value = False

        with pytest.raises(HTTPUnauthorized):
            svc.get_request_assignment(pyramid_request)

    def test_get_request_assignment_for_staff(
        self, pyramid_request, assignment_service, pyramid_config, svc
    ):
        pyramid_config.testing_securitypolicy(permissive=True)
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        assignment_service.is_member.return_value = False

        assert svc.get_request_assignment(pyramid_request)

    def test_get_request_assignment(self, pyramid_request, assignment_service, svc):
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        assignment_service.is_member.return_value = True

        assert svc.get_request_assignment(pyramid_request)

        assignment_service.is_member.assert_called_once_with(
            assignment_service.get_by_id.return_value, pyramid_request.user.h_userid
        )

    def test_get_request_course_404(
        self,
        pyramid_request,
        course_service,
        svc,
    ):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            svc.get_request_course(pyramid_request)

    def test_get_request_course_403(self, pyramid_request, course_service, svc):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course_service.is_member.return_value = False

        with pytest.raises(HTTPUnauthorized):
            svc.get_request_course(pyramid_request)

    def test_get_request_course_for_staff(
        self, pyramid_request, course_service, pyramid_config, svc
    ):
        pyramid_config.testing_securitypolicy(permissive=True)
        pyramid_request.matchdict["course_id"] = sentinel.id
        course_service.is_member.return_value = False

        assert svc.get_request_course(pyramid_request)

    def test_get_request_course(self, pyramid_request, course_service, svc):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course_service.is_member.return_value = True

        assert svc.get_request_course(pyramid_request)

    def test_get_request_organizations_403(
        self,
        pyramid_request,
        organization_service,
        svc,
    ):
        organization_service.is_member.return_value = False

        with pytest.raises(HTTPUnauthorized):
            svc.get_request_organizations(pyramid_request)

    def test_get_request_organizations_for_staff(
        self, pyramid_request, pyramid_config, svc, db_session
    ):
        org = factories.Organization()
        svc.add_dashboard_admin(org, "test@example.com", "creator")
        db_session.flush()
        pyramid_request.lti_user = None
        pyramid_config.testing_securitypolicy(
            permissive=False,
            identity=Identity(userid="test@example.com", permissions=[]),
        )
        assert svc.get_request_organizations(pyramid_request) == [org]

    def test_get_request_organizations(
        self, pyramid_request, organization_service, svc, lti_user
    ):
        pyramid_request.lti_user = lti_user
        organization_service.is_member.return_value = True

        assert svc.get_request_organizations(pyramid_request) == [
            pyramid_request.lti_user.application_instance.organization
        ]

    def test_add_dashboard_admin(self, svc, db_session):
        admin = svc.add_dashboard_admin(
            factories.Organization(), "testing@example.com", "creator"
        )

        assert db_session.query(DashboardAdmin).one() == admin

    def test_delete_dashboard_admin(self, svc, db_session):
        admin = svc.add_dashboard_admin(
            factories.Organization(), "testing@example.com", "creator"
        )
        db_session.flush()

        svc.delete_dashboard_admin(admin.id)

        assert not db_session.query(DashboardAdmin).filter_by(id=admin.id).first()

    @pytest.fixture()
    def svc(self, assignment_service, course_service, organization_service, db_session):
        return DashboardService(
            db_session, assignment_service, course_service, organization_service
        )

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
        db_session,
    ):
        service = factory(sentinel.context, pyramid_request)

        DashboardService.assert_called_once_with(
            db=db_session,
            assignment_service=assignment_service,
            course_service=course_service,
            organization_service=organization_service,
        )
        assert service == DashboardService.return_value

    @pytest.fixture
    def DashboardService(self, patch):
        return patch("lms.services.dashboard.DashboardService")
