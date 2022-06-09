from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

AssignmentGrouping = make_factory(
    models.AssignmentGrouping, FACTORY_CLASS=SQLAlchemyModelFactory
)
