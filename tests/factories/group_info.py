from factory import Faker, SubFactory, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.application_instance import ApplicationInstance

GroupInfo = make_factory(
    models.GroupInfo,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    authority_provided_id=Faker("hexify", text="^" * 40),
    application_instance=SubFactory(ApplicationInstance),
)
