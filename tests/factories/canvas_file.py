from factory import Faker, SubFactory, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories import ApplicationInstance
from tests.factories.attributes import TOOL_CONSUMER_INSTANCE_GUID

CanvasFile = make_factory(
    models.CanvasFile,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    application_instance=SubFactory(ApplicationInstance),
    tool_consumer_instance_guid=TOOL_CONSUMER_INSTANCE_GUID,
    file_id=Faker("random_int"),
    course_id=Faker("random_int"),
    filename=Faker("file_name", extension="pdf"),
    size=Faker("random_int"),
)
