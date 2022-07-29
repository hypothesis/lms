import functools
import os
from unittest import mock

import factory.random
import pytest
import sqlalchemy

from lms import db


def get_test_database_url(default):
    return os.environ.get("TEST_DATABASE_URL", default)


TEST_SETTINGS = {
    "dev": False,
    "via_url": "http://TEST_VIA_SERVER.is/",
    "jwt_secret": "test_secret",
    "google_client_id": "fake_client_id",
    "google_developer_key": "fake_developer_key",
    "google_app_id": "fake_app_id",
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
    "h_authority": "TEST_AUTHORITY",
    "h_api_url_public": "https://h.example.com/api/",
    "h_api_url_private": "https://h.example.com/private/api/",
    "rpc_allowed_origins": ["http://localhost:5000"],
    "oauth2_state_secret": "test_oauth2_state_secret",
    "session_cookie_secret": "notasecret",
    "via_secret": "not_a_secret",
    "blackboard_api_client_id": "test_blackboard_api_client_id",
    "blackboard_api_client_secret": "test_blackboard_api_client_secret",
    "vitalsource_api_key": "test_vs_api_key",
}


@pytest.fixture(scope="session")
def db_engine():
    engine = sqlalchemy.create_engine(TEST_SETTINGS["database_url"])

    # Delete all database tables and re-initialize the database schema based on
    # the current models. Doing this at the beginning of each test run ensures
    # that any schema changes made to the models since the last test run will
    # be applied to the test DB schema before running the tests again.
    db.init(engine, drop=True, stamp=False)

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


@pytest.fixture(scope="session", autouse=True)
def factory_boy_random_seed():
    # Set factory_boy's random seed so that it produces the same random values
    # in each run of the tests.
    # See: https://factoryboy.readthedocs.io/en/latest/index.html#reproducible-random-values
    factory.random.reseed_random("hypothesis/lms")
