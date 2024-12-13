import contextlib
import functools
import json
import os
import re
from urllib.parse import urlencode

import httpretty
import oauthlib.oauth1
import pytest
from _pytest.monkeypatch import MonkeyPatch
from h_matchers import Any
from h_testkit import set_factoryboy_sqlalchemy_session
from sqlalchemy import text
from webtest import TestApp

from lms import db
from lms.app import create_app
from tests import factories
from tests.conftest import TEST_SETTINGS

TEST_SETTINGS["database_url"] = os.environ["DATABASE_URL"]

TEST_ENVIRONMENT = {
    key.upper(): value for key, value in TEST_SETTINGS.items() if isinstance(value, str)
}
TEST_ENVIRONMENT.update(
    {"RPC_ALLOWED_ORIGINS": ",".join(TEST_SETTINGS["rpc_allowed_origins"])}
)


@pytest.fixture
def environ():
    environ = dict(os.environ)
    environ.update(TEST_ENVIRONMENT)

    return environ


@pytest.fixture(autouse=True)
def clean_database(db_engine):
    """Delete any data added by the previous test."""
    tables = reversed(db.Base.metadata.sorted_tables)
    with contextlib.closing(db_engine.connect()) as conn:
        transaction = conn.begin()
        tnames = ", ".join('"' + t.name + '"' for t in tables)
        conn.execute(text(f"TRUNCATE {tnames};"))
        transaction.commit()


@pytest.fixture(scope="session")
def monkeysession():
    # It's planned to include this on pytest directly
    # https://github.com/pytest-dev/pytest/issues/363
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope="session")
def pyramid_app():
    return create_app(None, **TEST_SETTINGS)


@pytest.fixture
def app(pyramid_app):
    return TestApp(pyramid_app)


@pytest.fixture
def db_session(db_engine, db_sessionfactory):
    """Get a standalone database session for preparing database state."""

    connection = db_engine.connect()
    session = db_sessionfactory(bind=connection)

    set_factoryboy_sqlalchemy_session(session, persistence="commit")

    try:
        yield session
    finally:
        session.close()
        connection.close()


def _lti_v11_launch(app, url, post_params, get_params=None, **kwargs):
    if get_params:
        url += f"?{urlencode(get_params)}"

    return app.post(
        url,
        params=post_params,
        headers={
            "Accept": "text/html",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        **kwargs,
    )


@pytest.fixture
def do_lti_launch(app):
    return functools.partial(_lti_v11_launch, app, "/lti_launches")


@pytest.fixture
def do_deep_link_launch(app):
    return functools.partial(_lti_v11_launch, app, "/content_item_selection")


@pytest.fixture
def get_client_config():
    def _get_client_config(response):
        return json.loads(response.html.find("script", {"class": "js-config"}).string)

    return _get_client_config


@pytest.fixture
def application_instance(db_session):  # noqa: ARG001
    return factories.ApplicationInstance(
        tool_consumer_instance_guid="IMS Testing",
        organization=factories.Organization(),
    )


@pytest.fixture
def oauth_client(application_instance):
    return oauthlib.oauth1.Client(
        application_instance.consumer_key, application_instance.shared_secret
    )


@pytest.fixture(autouse=True)
def intercept_http_calls_to_h():
    """
    Monkey-patch Python's socket core module to mock all HTTP responses.

    We will catch calls to H's API and return 200. All other calls will
    raise an exception, allowing to you see who we are trying to call.
    """

    # Catch URLs we aren't expecting or have failed to mock
    def error_response(request, uri, _response_headers):
        raise NotImplementedError(f"Unexpected call to URL: {request.method} {uri}")

    with httpretty.enabled():
        # Mock all calls to the H API
        httpretty.register_uri(
            method=Any(), uri=re.compile(r"^https://h.example.com/.*"), body=""
        )

        httpretty.register_uri(method=Any(), uri=re.compile(".*"), body=error_response)

        yield
