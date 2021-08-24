import factory
from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories import ApplicationInstance
from tests.factories.attributes import TOOL_CONSUMER_INSTANCE_GUID, USER_ID

LTIUser = make_factory(
    models.LTIUser,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    user_id=USER_ID,
    roles=Faker("random_element", elements=["Learner", "Instructor"]),
    tool_consumer_instance_guid=TOOL_CONSUMER_INSTANCE_GUID,
    application_instance=factory.SubFactory(ApplicationInstance),
    display_name=Faker("name"),
    email=factory.LazyAttribute(
        lambda a: "{}@lms.edu".format(a.display_name.replace(" ", "")).lower()
    ),
)
