import logging

import sqlalchemy
import zope.sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.properties import ColumnProperty

__all__ = ("BASE", "init")


log = logging.getLogger(__name__)


class BaseClass:
    """Functions common to all SQL Alchemy models."""

    @classmethod
    def iter_properties(cls):
        """Iterate over all declared SQL Alchemy properties."""
        return inspect(cls).iterate_properties

    @classmethod
    def iter_columns(cls):
        """Iterate over all declared SQL Alchemy columns."""
        return (
            property
            for property in cls.iter_properties()
            if isinstance(property, ColumnProperty)
        )


BASE = declarative_base(
    # Create a default metadata object with naming conventions for indexes and
    # constraints. This makes changing such constraints and indexes with
    # alembic after creation much easier. See:
    #
    #   http://docs.sqlalchemy.org/en/latest/core/constraints.html#configuring-constraint-naming-conventions
    #
    cls=BaseClass,
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


SESSION = sessionmaker()


def init(engine):
    """Initialise the database tables."""
    BASE.metadata.create_all(engine)


def make_engine(settings):
    """Construct a sqlalchemy engine from the passed ``settings``."""
    return sqlalchemy.create_engine(settings["sqlalchemy.url"])


def _session(request):
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
    def close_the_sqlalchemy_session(_request):  # pylint: disable=unused-variable
        connections = (
            session.transaction._connections  # pylint:disable=protected-access
        )
        if len(connections) > 1:
            log.warning("closing an unclosed DB session")
        session.close()

    return session


def includeme(config):
    # Create the SQLAlchemy engine and save a reference in the app registry.
    engine = make_engine(config.registry.settings)
    config.registry["sqlalchemy.engine"] = engine
    init(engine)

    # Add a property to all requests for easy access to the session. This means
    # that view functions need only refer to ``request.db`` in order to
    # retrieve the current database session.
    config.add_request_method(_session, name="db", reify=True)
