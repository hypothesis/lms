import functools
import os
from unittest import mock

import pytest
import sqlalchemy
from filelock import FileLock

from lms import db


def get_database_url():
    return os.environ.get("DATABASE_URL")


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


@pytest.fixture(scope="session")
def db_engine(tmp_path_factory):
    engine = sqlalchemy.create_engine(TEST_SETTINGS["database_url"])

    # Use a filelock to only init the DB once even though we have multiple
    # parallel pytest-xdist workers. See:
    # https://pytest-xdist.readthedocs.io/en/stable/how-to.html#making-session-scoped-fixtures-execute-only-once

    # The temporary directory shared by all pytest-xdist workers.
    shared_tmpdir = tmp_path_factory.getbasetemp().parent

    # The existence of this file records that a worker has initialized the DB.
    done_file = shared_tmpdir / "db_initialized.done"

    # The lock file prevents workers from entering the `with` at the same time.
    lock_file = shared_tmpdir / "db_initialized.lock"

    with FileLock(str(lock_file)):
        if done_file.is_file():
            # Another worker already initialized the DB.
            pass
        else:
            # Delete all database tables and re-initialize the database schema
            # based on the current models. Doing this at the beginning of each
            # test run ensures that any schema changes made to the models since
            # the last test run will be applied to the test DB schema before
            # running the tests again.
            db.init(engine, drop=True, stamp=False)

            # Make sure that no other worker tries to init the DB after we
            # release the lock file.
            done_file.touch()

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
