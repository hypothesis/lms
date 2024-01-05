import contextlib
import re
from os import environ
from urllib.parse import urlencode

import httpretty
import pytest
from _pytest.monkeypatch import MonkeyPatch
from h_matchers import Any
from sqlalchemy import text
from webtest import TestApp

from lms import db
from lms.app import create_app
from lms.db import SESSION
from tests import factories
from tests.conftest import TEST_SETTINGS

TEST_SETTINGS["database_url"] = environ["DATABASE_URL"]

TEST_ENVIRONMENT = {
    key.upper(): value for key, value in TEST_SETTINGS.items() if isinstance(value, str)
}
TEST_ENVIRONMENT.update(
    {"RPC_ALLOWED_ORIGINS": ",".join(TEST_SETTINGS["rpc_allowed_origins"])}
)


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
def db_session(db_engine):
    """Get a standalone database session for preparing database state."""

    conn = db_engine.connect()
    session = SESSION(bind=conn)

    factories.set_sqlalchemy_session(session, persistence="commit")

    try:
        yield session
    finally:
        factories.clear_sqlalchemy_session()
        session.close()
        conn.close()


@pytest.fixture
def do_lti_launch(app):
    def do_lti_launch(post_params, get_params=None, **kwargs):
        url = "/lti_launches"
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

    return do_lti_launch


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
