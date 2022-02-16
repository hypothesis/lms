from unittest.mock import create_autospec, sentinel

import pytest
import requests

from lms.services.canvas_api._authenticated import AuthenticatedClient
from lms.services.canvas_api._basic import BasicClient


@pytest.fixture
def basic_client(http_session):
    return BasicClient("canvas_host", session=http_session)


@pytest.fixture
def http_session():
    return create_autospec(requests.Session, spec_set=True, instance=True)


@pytest.fixture
def authenticated_client(basic_client, oauth2_token_service):
    return AuthenticatedClient(
        basic_client=basic_client,
        oauth2_token_service=oauth2_token_service,
        client_id=sentinel.client_id,
        client_secret=sentinel.client_secret,
        redirect_uri=sentinel.redirect_uri,
        refresh_enabled=True,
    )
