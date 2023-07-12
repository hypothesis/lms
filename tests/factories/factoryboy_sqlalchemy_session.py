import sys

from factory.alchemy import SQLAlchemyModelFactory


def set_factoryboy_sqlalchemy_session(session, persistence=None):
    # Set the Meta.sqlalchemy_session option on all our SQLAlchemy test factory
    # classes. We can't do it in the normal Factory Boy way:
    #
    #     class MyFactory:
    #         class Meta:
    #             sqlalchemy_session = session
    #
    # Because we don't have `session` available to us at import time.
    # So we have to do it this way instead.
    #
    # See:
    # https://factoryboy.readthedocs.io/en/latest/orms.html#sqlalchemy
    # https://factoryboy.readthedocs.io/en/latest/reference.html#factory.Factory._meta
    for factory_class in _sqlalchemy_factory_classes():
        # pylint:disable=protected-access
        factory_class._meta.sqlalchemy_session = session

        if persistence:
            factory_class._meta.sqlalchemy_session_persistence = persistence


def clear_factoryboy_sqlalchemy_session():
    # Delete the sqlalchemy session from all our test factories.
    # Just in case, so we don't have references to the session hanging about.
    for factory_class in _sqlalchemy_factory_classes():
        factory_class._meta.sqlalchemy_session = None  # pylint:disable=protected-access


def _sqlalchemy_factory_classes():
    """Return all the SQLAlchemy factory classes from tests.factories."""

    # Get the package that this module belongs to.
    package = sys.modules[sys.modules[__name__].__package__]

    for value in package.__dict__.values():
        try:
            is_sqla_factory = issubclass(value, SQLAlchemyModelFactory)
        except TypeError:
            is_sqla_factory = False

        if is_sqla_factory:
            yield value
