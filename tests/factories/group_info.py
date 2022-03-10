from factory import SubFactory, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.application_instance import ApplicationInstance

GroupInfo = make_factory(
    models.GroupInfo,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    application_instance=SubFactory(ApplicationInstance),
)
