import factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories._attributes import OAUTH_CONSUMER_KEY

Course = factory.make_factory(  # pylint:disable=invalid-name
    models.Course,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    consumer_key=OAUTH_CONSUMER_KEY,
    authority_provided_id=factory.Faker("hexify", text="^" * 40),
    _settings=factory.lazy_attribute(lambda o: {}),
)
