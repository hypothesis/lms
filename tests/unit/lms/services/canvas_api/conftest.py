from unittest.mock import sentinel

import pytest

from lms.services.canvas_api import AuthenticatedClient, BasicClient, TokenStore
from tests import factories


@pytest.fixture
def token_store(db_session, application_instance, lti_user):
    return TokenStore(
        db_session,
        consumer_key=application_instance.consumer_key,
        user_id=lti_user.user_id,
    )


@pytest.fixture
def basic_client():
    return BasicClient("canvas_host")


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
def application_instance(db_session):
    application_instance = factories.ApplicationInstance()
    db_session.add(application_instance)
    return application_instance


@pytest.fixture
def oauth_token(db_session, lti_user, application_instance):
    oauth_token = factories.OAuth2Token(
        user_id=lti_user.user_id, consumer_key=application_instance.consumer_key
    )
    db_session.add(oauth_token)
    return oauth_token
