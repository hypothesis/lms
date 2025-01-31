from unittest.mock import Mock, call, sentinel

import pytest

from lms.services.lti_names_roles import LTINamesRolesService, factory


class TestLTINameRolesServices:
    def test_get_context_memberships(self, svc, ltia_http_service, lti_registration):
        ltia_http_service.request.return_value.links = {}

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
            params={"limit": 100},
        )
        assert (
            memberships
            == ltia_http_service.request.return_value.json.return_value["members"]
        )

    def test_get_context_memberships_multiple_pages(
        self, svc, ltia_http_service, lti_registration
    ):
        ltia_http_service.request.side_effect = [
            Mock(
                links={"next": {"url": sentinel.next_url}},
                json=Mock(return_value={"members": [sentinel.member_1]}),
            ),
            Mock(
                links={},
                json=Mock(return_value={"members": [sentinel.member_2]}),
            ),
        ]

        memberships = svc.get_context_memberships(
            lti_registration, sentinel.service_url
        )

        ltia_http_service.request.assert_has_calls(
            [
                call(
                    lti_registration,
                    "GET",
                    sentinel.service_url,
                    scopes=LTINamesRolesService.LTIA_SCOPES,
                    headers={
                        "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json"
                    },
                    params={"limit": 100},
                ),
                call(
                    lti_registration,
                    "GET",
                    sentinel.next_url,
                    scopes=LTINamesRolesService.LTIA_SCOPES,
                    headers={
                        "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json"
                    },
                    params={"limit": 100},
                ),
            ]
        )
        assert memberships == [sentinel.member_1, sentinel.member_2]

    def test_get_context_memberships_with_resource_link_id(
        self, svc, ltia_http_service, lti_registration
    ):
        ltia_http_service.request.return_value.links = {}

        memberships = svc.get_context_memberships(
            lti_registration, sentinel.service_url, sentinel.resource_link_id
        )

        ltia_http_service.request.assert_called_once_with(
            lti_registration,
            "GET",
            sentinel.service_url,
            scopes=LTINamesRolesService.LTIA_SCOPES,
            headers={
                "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json"
            },
            params={"rlid": sentinel.resource_link_id, "limit": 100},
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
