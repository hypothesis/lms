from factory import Faker, Sequence, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.attributes import TOOL_CONSUMER_INSTANCE_GUID

LMSCourse = make_factory(
    models.LMSCourse,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    tool_consumer_instance_guid=TOOL_CONSUMER_INSTANCE_GUID,
    lti_context_id=Faker("hexify", text="^" * 40),
    h_authority_provided_id=Faker("hexify", text="^" * 40),
    name=Sequence(lambda n: f"Course {n}"),
)

LMSCourseApplicationInstance = make_factory(
    models.LMSCourseApplicationInstance, FACTORY_CLASS=SQLAlchemyModelFactory
)

LMSCourseMembership = make_factory(
    models.LMSCourseMembership, FACTORY_CLASS=SQLAlchemyModelFactory
)
