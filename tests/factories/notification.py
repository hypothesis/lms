from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

Notification = make_factory(
    models.Notification,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    source_annotation_id=Faker("hexify", text="^" * 40),
)
