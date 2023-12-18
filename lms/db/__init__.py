import logging

import alembic.command
import alembic.config
import sqlalchemy
import zope.sqlalchemy
from sqlalchemy import text
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm.properties import ColumnProperty

from lms.db._columns import varchar_enum
from lms.db._text_search import full_text_match

__all__ = ("BASE", "init", "varchar_enum")


BASE = declarative_base(
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


def init(engine, drop=False, stamp=True):  # pragma: nocover
    """
    Create all the database tables if they don't already exist.

    If `drop=True` is given then delete all existing tables first and then
    re-create them. Tests use this. If `drop=False` existing tables won't be
    touched.

    If `stamp=True` alembic's `alembic_version` will be overwritten with the latest revison
    in order to avoid alembic trying to re-create tables created by `create_all`

    :param engine: the sqlalchemy Engine object
    :param drop: whether or not to delete existing tables
    :param stamp: whether or not to stamp alembic latest revision
    """
    connection = engine.connect()
    try:
        connection.execute(text("select 1 from alembic_version"))
    except sqlalchemy.exc.ProgrammingError:
        connection.rollback()  # Rollback after failure to find the alembic table
        if drop:
            # SQLAlchemy doesnt' know about the report schema, and will end up
            # trying to drop tables without cascade that have dependent tables
            # in the report schema and failing. Clear it out first.
            connection.execute(text("DROP SCHEMA IF EXISTS report CASCADE"))
            BASE.metadata.drop_all(engine)
        BASE.metadata.create_all(engine)

        if stamp:
            alembic.command.stamp(alembic.config.Config("conf/alembic.ini"), "head")


def make_engine(settings):
    """Construct a sqlalchemy engine from the passed ``settings``."""
    return sqlalchemy.create_engine(settings["database_url"])


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
    engine = make_engine(config.registry.settings)
    config.registry["sqlalchemy.engine"] = engine

    if config.registry.settings["dev"]:  # pragma: nocover
        init(engine)

    # Add a property to all requests for easy access to the session. This means
    # that view functions need only refer to ``request.db`` in order to
    # retrieve the current database session.
    config.add_request_method(_session, name="db", reify=True)
