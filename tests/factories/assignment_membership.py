from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

AssignmentMembership = make_factory(
    models.AssignmentMembership, FACTORY_CLASS=SQLAlchemyModelFactory
)

LMSUserAssignmentMembership = make_factory(
    models.LMSUserAssignmentMembership, FACTORY_CLASS=SQLAlchemyModelFactory
)
