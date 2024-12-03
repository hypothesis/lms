import logging

import alembic.command
import alembic.config
import sqlalchemy
import zope.sqlalchemy
from sqlalchemy import Select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Query, Session, declarative_base, sessionmaker
from sqlalchemy.orm.properties import ColumnProperty

from lms.db._columns import varchar_enum
from lms.db._locks import CouldNotAcquireLock, LockType, try_advisory_transaction_lock
from lms.db._text_search import full_text_match
from lms.db._util import compile_query

__all__ = ("Base", "compile_query", "create_engine", "varchar_enum")


Base = declarative_base(
    # Create a default metadata object with naming conventions for indexes and
    # constraints. This makes changing such constraints and indexes with
    # alembic after creation much easier. See:
    #
    #   http://docs.sqlalchemy.org/en/latest/core/constraints.html#configuring-constraint-naming-conventions
    #
    metadata=sqlalchemy.MetaData(
        naming_convention={
            "ix": "ix__%(column_0_label)s",
            "uq": "uq__%(table_name)s__%(column_0_name)s",
            "ck": "ck__%(table_name)s__%(constraint_name)s",
            "fk": "fk__%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
            "pk": "pk__%(table_name)s",
        }
    ),
)


def create_engine(database_url):
    """Construct a sqlalchemy engine from the passed ``settings``."""
    return sqlalchemy.create_engine(database_url)


SESSION = sessionmaker()


def _session(request):  # pragma: no cover
    engine = request.registry["sqlalchemy.engine"]
    session = SESSION(bind=engine)

    # If the request has a transaction manager, associate the session with it.
    try:
        transaction_manager = request.tm
    except AttributeError:
        pass
    else:
        zope.sqlalchemy.register(session, transaction_manager=transaction_manager)

    # pyramid_tm doesn't always close the database session for us.
    #
    # If anything that executes later in the Pyramid request processing cycle
    # than pyramid_tm tween egress opens a new DB session (for example a tween
    # above the pyramid_tm tween, a response callback, or a NewResponse
    # subscriber) then pyramid_tm won't close that DB session for us.
    #
    # So as a precaution add our own callback here to make sure db sessions are
    # always closed.
    @request.add_finished_callback
    def close_the_sqlalchemy_session(_request):
        session.close()

    return session


def includeme(config):
    # Create the SQLAlchemy engine and save a reference in the app registry.
    engine = create_engine(config.registry.settings["database_url"])
    config.registry["sqlalchemy.engine"] = engine

    # Add a property to all requests for easy access to the session. This means
    # that view functions need only refer to ``request.db`` in order to
    # retrieve the current database session.
    config.add_request_method(_session, name="db", reify=True)
