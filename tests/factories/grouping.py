import factory
from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory
from tests.factories import ApplicationInstance

from lms import models
from tests.factories.attributes import OAUTH_CONSUMER_KEY, SHARED_SECRET

Grouping = make_factory(
    models.Grouping,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    application_instance=factory.SubFactory(ApplicationInstance),
    authority_provided_id=factory.Faker("hexify", text="^" * 40),
    lms_id=factory.Faker("hexify", text="^" * 40),
)
