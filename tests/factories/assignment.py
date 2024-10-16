from factory import Faker, Sequence, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.attributes import RESOURCE_LINK_ID, TOOL_CONSUMER_INSTANCE_GUID

Assignment = make_factory(
    models.Assignment,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    resource_link_id=RESOURCE_LINK_ID,
    tool_consumer_instance_guid=TOOL_CONSUMER_INSTANCE_GUID,
    document_url=Faker("uri"),
    extra={},
    title=Sequence(lambda n: f"Assignment {n}"),
)


AutoGradingConfig = make_factory(
    models.AutoGradingConfig,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    activity_calculation=Faker("random_element", elements=list(models.AutoGradingType)),
    grading_type=Faker("random_element", elements=list(models.AutoGradingCalculation)),
    required_annotations=Faker("random_int"),
    required_replies=Faker("random_int"),
)
