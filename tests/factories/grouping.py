import factory
from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories import ApplicationInstance

Grouping = make_factory(
    models.Grouping,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    application_instance=factory.SubFactory(ApplicationInstance),
    authority_provided_id=factory.Faker("hexify", text="^" * 40),
    lms_id=factory.Faker("hexify", text="^" * 40),
    lms_name=factory.Sequence(lambda n: f"Test Group {n}"),
)
