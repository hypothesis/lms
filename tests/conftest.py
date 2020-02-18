import functools
import os
from unittest import mock

import pytest
import sqlalchemy
from sqlalchemy.orm import sessionmaker

from lms import db

SESSION = sessionmaker()


def get_test_database_url(default):
    return os.environ.get("TEST_DATABASE_URL", default)


TEST_SETTINGS = {
    "via_url": "http://TEST_VIA_SERVER.is/",
    "via3_url": "http://TEST_VIA3_SERVER.is/",
    "jwt_secret": "test_secret",
    "google_client_id": "fake_client_id",
    "google_developer_key": "fake_developer_key",
    "google_app_id": "fake_app_id",
    "lms_secret": "TEST_LMS_SECRET",
    "hashed_pw": "e46df2a5b4d50e259b5154b190529483a5f8b7aaaa22a50447e377d33792577a",
    "salt": "fbe82ee0da72b77b",
    "username": "report_viewer",
    "aes_secret": b"TSeQ7E3dzbHgu5ydX2xCrKJiXTmfJbOe",
    "jinja2.filters": {
        "static_path": "pyramid_jinja2.filters:static_path_filter",
        "static_url": "pyramid_jinja2.filters:static_url_filter",
    },
    "h_client_id": "TEST_CLIENT_ID",
    "h_client_secret": "TEST_CLIENT_SECRET",
    "h_jwt_client_id": "TEST_JWT_CLIENT_ID",
    "h_jwt_client_secret": "TEST_JWT_CLIENT_SECRET",
    "h_authority": "TEST_AUTHORITY",
    "h_api_url_public": "https://example.com/api/",
    "h_api_url_private": "https://example.com/private/api/",
    "rpc_allowed_origins": ["http://localhost:5000"],
    "oauth2_state_secret": "test_oauth2_state_secret",
    "session_cookie_secret": "notasecret",
}


@pytest.fixture(scope="session")
def db_engine():
    engine = sqlalchemy.create_engine(TEST_SETTINGS["sqlalchemy.url"])

    # Delete all database tables and re-initialize the database schema based on
    # the current models. Doing this at the beginning of each test run ensures
    # that any schema changes made to the models since the last test run will
    # be applied to the test DB schema before running the tests again.
    db.init(engine, drop=True)

    return engine


def autopatcher(request, target, **kwargs):
    """Patch and cleanup automatically. Wraps :py:func:`mock.patch`."""
    options = {"autospec": True}
    options.update(kwargs)
    patcher = mock.patch(target, **options)
    obj = patcher.start()
    request.addfinalizer(patcher.stop)
    return obj


@pytest.fixture
def patch(request):
    return functools.partial(autopatcher, request)
