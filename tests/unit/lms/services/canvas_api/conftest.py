from unittest.mock import sentinel

import pytest

from lms.services.canvas_api._authenticated import AuthenticatedClient
from lms.services.canvas_api._basic import BasicClient
from tests import factories


@pytest.fixture
def basic_client():
    return BasicClient("canvas_host")


@pytest.fixture
def http_session(patch):
    session = patch("lms.services.canvas_api._basic.Session")
    session = session()

    def set_response(json_data=None, raw=None, status_code=200):
        session.send.return_value = factories.requests.Response(
            json_data=json_data, raw=raw, status_code=status_code
        )

    session.set_response = set_response

    return session


@pytest.fixture
def authenticated_client(basic_client, token_store_service):
    return AuthenticatedClient(
        basic_client=basic_client,
        token_store=token_store_service,
        client_id=sentinel.client_id,
        client_secret=sentinel.client_secret,
        redirect_uri=sentinel.redirect_uri,
    )
