import contextlib

import pytest
from _pytest.monkeypatch import MonkeyPatch
from webtest import TestApp

from lms import db
from lms.app import create_app
from tests import factories
from tests.conftest import SESSION, TEST_SETTINGS, get_test_database_url

TEST_SETTINGS["sqlalchemy.url"] = get_test_database_url(
    default="postgresql://postgres@localhost:5433/lms_functests"
)


@pytest.fixture(autouse=True)
def clean_database(db_engine):
    """Delete any data added by the previous test."""
    tables = reversed(db.BASE.metadata.sorted_tables)
    with contextlib.closing(db_engine.connect()) as conn:
        transaction = conn.begin()
        tnames = ", ".join('"' + t.name + '"' for t in tables)
        conn.execute("TRUNCATE {};".format(tnames))
        transaction.commit()


@pytest.fixture(scope="session")
def monkeysession():
    # It's planned to include this on pytest directly
    # https://github.com/pytest-dev/pytest/issues/363
    mpatch = MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope="session")
def pyramid_app(environment):  # pylint: disable=unused-argument
    return create_app(None, **TEST_SETTINGS)


@pytest.fixture
def app(pyramid_app, db_engine):
    db.init(db_engine)

    return TestApp(pyramid_app)


@pytest.fixture(scope="session")
def environment(monkeysession):
    monkeysession.setenv("LMS_SECRET", TEST_SETTINGS["lms_secret"])
    monkeysession.setenv("USERNAME", TEST_SETTINGS["username"])


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
