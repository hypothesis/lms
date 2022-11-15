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

    @pytest.fixture
    def basic_client(self):
        return create_autospec(BasicClient, instance=True, spec_set=True)

    @pytest.fixture
    def svc(self, basic_client, pyramid_request):
        return D2LAPIClient(basic_client, pyramid_request)
