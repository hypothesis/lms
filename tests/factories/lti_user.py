from factory import Faker, make_factory

from lms import models
from tests.factories.attributes import TOOL_CONSUMER_INSTANCE_GUID, USER_ID

LTIUser = make_factory(
    models.LTIUser,
    user_id=USER_ID,
    roles=Faker("random_element", elements=["Learner", "Instructor"]),
    lti_roles=[],
    tool_consumer_instance_guid=TOOL_CONSUMER_INSTANCE_GUID,
    display_name=Faker("name"),
)
