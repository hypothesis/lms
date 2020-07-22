import factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories import ApplicationInstance

Course = factory.make_factory(  # pylint:disable=invalid-name
    models.Course,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    application_instance=factory.SubFactory(ApplicationInstance),
    authority_provided_id=factory.Faker("hexify", text="^" * 40),
)
