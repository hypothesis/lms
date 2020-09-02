from unittest.mock import create_autospec, sentinel

import pytest

from lms.services.canvas_api._authenticated import AuthenticatedClient
from lms.services.canvas_api._basic import BasicClient
from lms.services.canvas_api._token_store import TokenStore
from tests import factories


@pytest.fixture
def token_store(oauth_token):
    token_store = create_autospec(TokenStore, spec_set=True, instance=True)
    token_store.get.return_value = oauth_token
    return token_store


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
def authenticated_client(basic_client, token_store):
    return AuthenticatedClient(
        basic_client=basic_client,
        token_store=token_store,
        client_id=sentinel.client_id,
        client_secret=sentinel.client_secret,
        redirect_uri=sentinel.redirect_uri,
    )


@pytest.fixture
def lti_user():
    return factories.LTIUser()


@pytest.fixture
def application_instance():
    return factories.ApplicationInstance()


@pytest.fixture
def oauth_token(lti_user, application_instance):
    return factories.OAuth2Token(
        user_id=lti_user.user_id, application_instance=application_instance
    )
