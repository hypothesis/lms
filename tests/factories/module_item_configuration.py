from factory import Dict, Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.attributes import RESOURCE_LINK_ID, TOOL_CONSUMER_INSTANCE_GUID

ModuleItemConfiguration = make_factory(
    models.ModuleItemConfiguration,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    resource_link_id=RESOURCE_LINK_ID,
    tool_consumer_instance_guid=TOOL_CONSUMER_INSTANCE_GUID,
    document_url=Faker("uri"),
    extra=Dict({}),
)
