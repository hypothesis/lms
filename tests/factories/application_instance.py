from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.attributes import (
    OAUTH_CONSUMER_KEY,
    SHARED_SECRET,
    TOOL_CONSUMER_INSTANCE_GUID,
)

ApplicationInstance = make_factory(
    models.ApplicationInstance,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    name=Faker("company"),
    consumer_key=OAUTH_CONSUMER_KEY,
    shared_secret=SHARED_SECRET,
    lms_url=Faker("url", schemes=["https"]),
    requesters_email=Faker("email"),
    settings={},
    tool_consumer_instance_guid=TOOL_CONSUMER_INSTANCE_GUID,
)
