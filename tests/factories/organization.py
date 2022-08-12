from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

Organization = make_factory(
    models.Organization,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    name=Faker("company"),
    settings={},
)
