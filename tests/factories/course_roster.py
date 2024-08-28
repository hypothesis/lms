from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

CourseRoster = make_factory(models.CourseRoster, FACTORY_CLASS=SQLAlchemyModelFactory)
