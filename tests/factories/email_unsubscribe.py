from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

EmailUnsubscribe = make_factory(
    models.EmailUnsubscribe,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    tag=Faker("word"),
    email=Faker("email"),
)
