import logging
from functools import cached_property

import alembic.command
import alembic.config
import sqlalchemy
import zope.sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm.properties import ColumnProperty

from lms.db._columns import varchar_enum

__all__ = ("BASE", "init", "varchar_enum")


LOG = logging.getLogger(__name__)


class BaseClass:
    """Functions common to all SQLAlchemy models."""

    @classmethod
    def columns(cls):
        """Return a list of all declared SQLAlchemy column names."""
        return [
            property.key
            for property in inspect(cls).iterate_properties
            if isinstance(property, ColumnProperty)
        ]

    def update_from_dict(self, data, skip_keys=None):
        """
        Update this model from the provided dict.

        Any keys listed in ``skip_keys`` will *not* be updated, even if they are in ``data``.

        :param data: The data to update
        :param skip_keys: A set of keys to exclude from being updated (default: {"id"})
        :type skip_keys: set[str]

        :raise TypeError: if skip_keys isn't a set
        """

        if skip_keys is None:
            skip_keys = {"id"}

        if not isinstance(skip_keys, set):
            raise TypeError(
                f"Expected a set of keys to skip but found '{type(skip_keys)}'"
            )

        columns = set(self.columns())
        columns -= skip_keys

        for key in columns:
            if key in data:
                setattr(self, key, data[key])

    def __repr__(self):
        return "{class_}({kwargs})".format(  # pylint: disable=consider-using-f-string
            class_=self.__class__.__name__,
            kwargs=", ".join(
                f"{kwarg}={repr(getattr(self, kwarg))}"
                for kwarg in self.__table__.columns.keys()  # pylint:disable=no-member
            ),
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
    try:
        engine.execute("select 1 from alembic_version")
    except sqlalchemy.exc.ProgrammingError:
        if drop:
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
        connections = (
            session.transaction._connections  # pylint:disable=protected-access
        )
        if len(connections) > 1:
            LOG.warning("closing an unclosed DB session")
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
