import factory
from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from lms.services.grouping import GroupingService
from tests.factories import ApplicationInstance

Grouping = make_factory(
    models.Grouping,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    application_instance=factory.SubFactory(ApplicationInstance),
    authority_provided_id=factory.LazyAttribute(
        lambda obj: GroupingService.generate_authority_provided_id(
            obj.application_instance.tool_consumer_instance_guid,
            obj.lms_id,
            None,
            obj.type,
        )
    ),
    lms_id=factory.Faker("hexify", text="^" * 40),
    lms_name=factory.Sequence(lambda n: f"Test Group {n}"),
    type=models.Grouping.Type.GROUPING,
)
