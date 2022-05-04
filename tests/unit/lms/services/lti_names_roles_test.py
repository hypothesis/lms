from unittest.mock import sentinel

import pytest

from lms.services.lti_names_roles import LTINamesRolesService, factory


class TestLTINameRolesServices:
    def test_get_context_memberships(self, svc, ltia_http_service):

        memberships = svc.get_context_memberships()

        ltia_http_service.request.assert_called_once_with(
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
        return LTINamesRolesService(
            service_url=sentinel.service_url, ltia_http_service=ltia_http_service
        )


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        LTINamesRolesService,
        ltia_http_service,
    ):
        service = factory(sentinel.context, pyramid_request)

        LTINamesRolesService.assert_called_once_with(
            service_url=sentinel.service_url, ltia_http_service=ltia_http_service
        )
        assert service == LTINamesRolesService.return_value

    @pytest.fixture
    def LTINamesRolesService(self, patch):
        return patch("lms.services.lti_names_roles.LTINamesRolesService")

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.lti_jwt = {
            "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice": {
                "context_memberships_url": sentinel.service_url
            }
        }
        return pyramid_request
