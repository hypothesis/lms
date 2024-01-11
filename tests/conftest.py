import functools
from os import environ
from unittest import mock

import pytest
from sqlalchemy.orm import sessionmaker

from lms.db import create_engine
from tests import factories

TEST_SETTINGS = {
    "dev": False,
    "via_url": "http://TEST_VIA_SERVER.is/",
    "jwt_secret": "test_secret",
    "google_client_id": "fake_client_id",
    "google_developer_key": "fake_developer_key",
    "lms_secret": "TEST_LMS_SECRET",
    "aes_secret": b"TSeQ7E3dzbHgu5ydX2xCrKJiXTmfJbOe",
    "jinja2.filters": {
        "static_path": "pyramid_jinja2.filters:static_path_filter",
        "static_url": "pyramid_jinja2.filters:static_url_filter",
    },
    "h_client_id": "TEST_CLIENT_ID",
    "h_client_secret": "TEST_CLIENT_SECRET",
    "h_jwt_client_id": "TEST_JWT_CLIENT_ID",
    "h_jwt_client_secret": "TEST_JWT_CLIENT_SECRET",
    "h_authority": "lms.hypothes.is",
    "region_code": "us",
    "h_api_url_public": "https://h.example.com/api/",
    "h_api_url_private": "https://h.example.com/private/api/",
    "rpc_allowed_origins": ["http://localhost:5000"],
    "oauth2_state_secret": "test_oauth2_state_secret",
    "session_cookie_secret": "notasecret",
    "via_secret": "not_a_secret",
    "blackboard_api_client_id": "test_blackboard_api_client_id",
    "blackboard_api_client_secret": "test_blackboard_api_client_secret",
    "vitalsource_api_key": "test_vs_api_key",
    "disable_key_rotation": False,
    "admin_users": [],
    "email_preferences_secret": "test_email_preferences_secret",
}


def autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {"autospec": True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture(scope="session")
def db_engine():
    return create_engine(environ["DATABASE_URL"])


@pytest.fixture(scope="session")
def db_sessionfactory():
    return sessionmaker()


@pytest.fixture
def db_session(db_engine, db_sessionfactory):
    """
    Return the SQLAlchemy database session.

    This returns a session that is wrapped in an external transaction that is
    rolled back after each test, so tests can't make database changes that
    affect later tests.  Even if the test (or the code under test) calls
    session.commit() this won't touch the external transaction.

    This is the same technique as used in SQLAlchemy's own CI:
    https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = db_sessionfactory(
        bind=connection, join_transaction_mode="create_savepoint"
    )
    factories.set_sqlalchemy_session(session)

    yield session

    factories.clear_sqlalchemy_session()
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def patch(request):
    return functools.partial(autopatcher, request)


@pytest.fixture(autouse=True)
def envvars(monkeypatch):
    # Because we (unfortunately) have code at the lowest level of our codebase
    # (in the models) that's reading these envvars directly from os.environ we
    # get lots of unit and functional tests across our test suite failing when
    # these envvars don't exist.
    #
    # So as a workaround this fixture makes sure that these envvars are set for
    # all tests.
    #
    # It would be better if our model code did not read os.environ, then we
    # wouldn't need this fixture.
    monkeypatch.setenv("REGION_CODE", "us")
    monkeypatch.setenv("H_AUTHORITY", "lms.hypothes.is")
