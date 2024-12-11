from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

Event = make_factory(models.Event, FACTORY_CLASS=SQLAlchemyModelFactory)
