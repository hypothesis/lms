import contextlib

import pytest
from webtest import TestApp

from lms import db
from tests.conftest import SESSION, TEST_SETTINGS, get_test_database_url

TEST_SETTINGS["sqlalchemy.url"] = get_test_database_url(
    default="postgresql://postgres@localhost:5433/lms_functests"
)


@pytest.fixture(scope="session", autouse=True)
def auto_use_dn(db_engine):
    # TODO - Is this right?
    return db_engine


def _clean_database(engine):
    tables = reversed(db.BASE.metadata.sorted_tables)
    with contextlib.closing(engine.connect()) as conn:
        tx = conn.begin()
        tnames = ", ".join('"' + t.name + '"' for t in tables)
        conn.execute("TRUNCATE {};".format(tnames))
        tx.commit()


@pytest.fixture(scope="session")
def pyramid_app():
    from lms.app import create_app

    return create_app(None, **TEST_SETTINGS)


@pytest.fixture
def app(pyramid_app, db_engine):
    _clean_database(db_engine)
    db.init(db_engine)

    return TestApp(pyramid_app)


@pytest.fixture
def db_session(db_engine):
    """Get a standalone database session for preparing database state."""

    conn = db_engine.connect()
    session = SESSION(bind=conn)

    yield session

    session.close()
