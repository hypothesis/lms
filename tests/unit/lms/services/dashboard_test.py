from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized

from lms.services.dashboard import DashboardService, factory

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

    def test_get_request_organization_404(
        self, pyramid_request, organization_service, svc
    ):
        pyramid_request.matchdict["organization_public_id"] = sentinel.id
        organization_service.get_by_public_id.return_value = None

        with pytest.raises(HTTPNotFound):
            svc.get_request_organization(pyramid_request)

    def test_get_request_organization_403(
        self,
        pyramid_request,
        organization_service,
        svc,
    ):
        pyramid_request.matchdict["organization_public_id"] = sentinel.id
        organization_service.is_member.return_value = False

        with pytest.raises(HTTPUnauthorized):
            svc.get_request_organization(pyramid_request)

    def test_get_request_organization_for_staff(
        self, pyramid_request, organization_service, pyramid_config, svc
    ):
        pyramid_config.testing_securitypolicy(permissive=True)
        pyramid_request.matchdict["organization_public_id"] = sentinel.id
        organization_service.is_member.return_value = False

        assert svc.get_request_organization(pyramid_request)

    def test_get_request_organization(self, pyramid_request, organization_service, svc):
        pyramid_request.matchdict["organization_public_id"] = sentinel.id
        organization_service.is_member.return_value = True

        assert svc.get_request_organization(pyramid_request)

    @pytest.fixture()
    def svc(self, assignment_service, course_service, organization_service):
        return DashboardService(
            assignment_service, course_service, organization_service
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
    ):
        service = factory(sentinel.context, pyramid_request)

        DashboardService.assert_called_once_with(
            assignment_service=assignment_service,
            course_service=course_service,
            organization_service=organization_service,
        )
        assert service == DashboardService.return_value

    @pytest.fixture
    def DashboardService(self, patch):
        return patch("lms.services.dashboard.DashboardService")
