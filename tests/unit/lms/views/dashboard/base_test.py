from unittest.mock import sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized

from lms.views.dashboard.base import (
    get_request_assignment,
    get_request_course,
    get_request_organization,
)

pytestmark = pytest.mark.usefixtures("h_api", "assignment_service")


class TestBase:
    def test_get_request_assignment_404(
        self,
        pyramid_request,
        assignment_service,
    ):
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        assignment_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            get_request_assignment(pyramid_request, assignment_service)

    def test_get_request_assignment_403(
        self,
        pyramid_request,
        assignment_service,
    ):
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        assignment_service.is_member.return_value = False

        with pytest.raises(HTTPUnauthorized):
            get_request_assignment(pyramid_request, assignment_service)

    def test_get_request_assignment_for_staff(
        self, pyramid_request, assignment_service, pyramid_config
    ):
        pyramid_config.testing_securitypolicy(permissive=True)
        pyramid_request.matchdict["assignment_id"] = sentinel.id
        assignment_service.is_member.return_value = False

        assert get_request_assignment(pyramid_request, assignment_service)

    def test_get_request_course_404(
        self,
        pyramid_request,
        course_service,
    ):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course_service.get_by_id.return_value = None

        with pytest.raises(HTTPNotFound):
            get_request_course(pyramid_request, course_service)

    def test_get_request_course_403(
        self,
        pyramid_request,
        course_service,
    ):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course_service.is_member.return_value = False

        with pytest.raises(HTTPUnauthorized):
            get_request_course(pyramid_request, course_service)

    def test_get_request_course_for_staff(
        self, pyramid_request, course_service, pyramid_config
    ):
        pyramid_config.testing_securitypolicy(permissive=True)
        pyramid_request.matchdict["course_id"] = sentinel.id
        course_service.is_member.return_value = False

        assert get_request_course(pyramid_request, course_service)

    def test_get_request_course(self, pyramid_request, course_service):
        pyramid_request.matchdict["course_id"] = sentinel.id
        course_service.is_member.return_value = True

        assert get_request_course(pyramid_request, course_service)

    def test_get_request_organization_404(
        self,
        pyramid_request,
        organization_service,
    ):
        pyramid_request.matchdict["public_id"] = sentinel.id
        organization_service.get_by_public_id.return_value = None

        with pytest.raises(HTTPNotFound):
            get_request_organization(pyramid_request, organization_service)

    def test_get_request_organization_403(
        self,
        pyramid_request,
        organization_service,
    ):
        pyramid_request.matchdict["public_id"] = sentinel.id
        organization_service.is_member.return_value = False

        with pytest.raises(HTTPUnauthorized):
            get_request_organization(pyramid_request, organization_service)

    def test_get_request_organization_for_staff(
        self, pyramid_request, organization_service, pyramid_config
    ):
        pyramid_config.testing_securitypolicy(permissive=True)
        pyramid_request.matchdict["public_id"] = sentinel.id
        organization_service.is_member.return_value = False

        assert get_request_organization(pyramid_request, organization_service)

    def test_get_request_organization(self, pyramid_request, organization_service):
        pyramid_request.matchdict["public_id"] = sentinel.id
        organization_service.is_member.return_value = True

        assert get_request_organization(pyramid_request, organization_service)

    @pytest.fixture(autouse=True)
    def pyramid_config(self, pyramid_config):
        pyramid_config.testing_securitypolicy(permissive=False)
        return pyramid_config
