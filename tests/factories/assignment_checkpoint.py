from factory import SubFactory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.assignment import Assignment


class AssignmentCheckpoint(SQLAlchemyModelFactory):
    class Meta:
        model = models.AssignmentCheckpoint

    assignment = SubFactory(Assignment)
