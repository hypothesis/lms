from unittest.mock import create_autospec, sentinel

import pytest

from lms.services.d2l_api._basic import BasicClient
from lms.services.d2l_api.client import D2LAPIClient


class TestD2LAPIClient:
    def test_get_token(self, svc, basic_client):
        svc.get_token(sentinel.authorization_code)

        basic_client.get_token.assert_called_once_with(sentinel.authorization_code)

    def test_refresh_access_token(self, svc, basic_client):
        svc.refresh_access_token()

        basic_client.refresh_access_token.assert_called_once_with()

    def test_course_group_sets(
        self, svc, basic_client, D2LGroupSetsSchema, d2l_group_sets_schema
    ):
        group_sets = svc.course_group_sets("COURSE_ID")

        basic_client.request.assert_called_once_with(
            "GET", "/COURSE_ID/groupcategories/"
        )
        D2LGroupSetsSchema.assert_called_once_with(basic_client.request.return_value)
        assert group_sets == d2l_group_sets_schema.parse.return_value

    @pytest.fixture(autouse=True)
    def D2LGroupSetsSchema(self, patch):
        return patch("lms.services.d2l_api.client.D2LGroupSetsSchema")

    @pytest.fixture
    def d2l_group_sets_schema(self, D2LGroupSetsSchema):
        return D2LGroupSetsSchema.return_value

    @pytest.fixture
    def basic_client(self):
        return create_autospec(BasicClient, instance=True, spec_set=True)

    @pytest.fixture
    def svc(self, basic_client, pyramid_request):
        return D2LAPIClient(basic_client, pyramid_request)
