import sys

from factory.alchemy import SQLAlchemyModelFactory

from tests.factories.course import Course
from tests.factories.grading_info import GradingInfo
from tests.factories.h_group import HGroup
from tests.factories.h_user import HUser
from tests.factories.lti_user import LTIUser


def set_sqlalchemy_session(session):
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


def clear_sqlalchemy_session():
    # Delete the sqlalchemy session from all our test factories.
    # Just in case, so we don't have references to the session hanging about.
    for factory_class in _sqlalchemy_factory_classes():
        factory_class._meta.sqlalchemy_session = None  # pylint:disable=protected-access


def _sqlalchemy_factory_classes():
    # Return all the SQLAlchemy factory classes from tests.factories.
    for factory_class in sys.modules[__name__].__dict__.values():
        try:
            is_sqla_factory = issubclass(factory_class, SQLAlchemyModelFactory)
        except TypeError:
            is_sqla_factory = False

        if is_sqla_factory:
            yield factory_class
