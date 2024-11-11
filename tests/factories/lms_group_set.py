from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

LMSGroupSet = make_factory(
    models.LMSGroupSet,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    lms_id=Faker("hexify", text="^" * 40),
    name=Faker("word"),
)
