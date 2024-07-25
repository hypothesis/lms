from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized

from lms.models.dashboard_admin import DashboardAdmin
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

    def test_get_organizations_by_admin_email(self, svc, db_session, organization):
        admin = factories.DashboardAdmin(
            organization=organization, email="testing@example.com", created_by="creator"
        )
        db_session.flush()

        assert svc.get_organizations_by_admin_email(admin.email) == [organization]

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
