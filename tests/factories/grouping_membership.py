from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

GroupingMembership = make_factory(
    models.GroupingMembership, FACTORY_CLASS=SQLAlchemyModelFactory
)
