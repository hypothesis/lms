from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

LMSGroupSet = make_factory(models.LMSGroupSet, FACTORY_CLASS=SQLAlchemyModelFactory)
