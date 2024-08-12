from unittest.mock import sentinel

import pytest

from lms.services.lti_names_roles import LTINamesRolesService, factory


class TestLTINameRolesServices:
    def test_get_context_memberships(self, svc, ltia_http_service, lti_registration):
        memberships = svc.get_context_memberships(
            lti_registration, sentinel.service_url
        )

        ltia_http_service.request.assert_called_once_with(
            lti_registration,
            "GET",
            sentinel.service_url,
            scopes=LTINamesRolesService.LTIA_SCOPES,
            headers={
                "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json"
            },
        )
        assert (
            memberships
            == ltia_http_service.request.return_value.json.return_value["members"]
        )

    @pytest.fixture
    def svc(self, ltia_http_service):
        return LTINamesRolesService(ltia_http_service=ltia_http_service)


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        LTINamesRolesService,
        ltia_http_service,
    ):
        service = factory(sentinel.context, pyramid_request)

        LTINamesRolesService.assert_called_once_with(
            ltia_http_service=ltia_http_service
        )
        assert service == LTINamesRolesService.return_value

    @pytest.fixture
    def LTINamesRolesService(self, patch):
        return patch("lms.services.lti_names_roles.LTINamesRolesService")
