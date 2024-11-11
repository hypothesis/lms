import factory
from factory import Faker
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

LMSSegment = factory.make_factory(
    models.LMSSegment,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    type=Faker("random_element", elements=models.Grouping.Type),
    lms_id=Faker("hexify", text="^" * 40),
    name=Faker("word"),
    h_authority_provided_id=Faker("hexify", text="^" * 40),
)
