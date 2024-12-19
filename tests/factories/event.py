from factory import SubFactory, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

Event = make_factory(models.Event, FACTORY_CLASS=SQLAlchemyModelFactory)


EventData = make_factory(
    models.EventData,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    event=SubFactory(Event),
)
