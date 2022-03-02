from factory import Faker, fuzzy, make_factory

from lms import models
from tests.factories.attributes import TOOL_CONSUMER_INSTANCE_GUID, USER_ID

LTIUser = make_factory(
    models.LTIUser,
    user_id=USER_ID,
    application_instance_id=fuzzy.FuzzyInteger(1, 9999999999),
    roles=Faker("random_element", elements=["Learner", "Instructor"]),
    tool_consumer_instance_guid=TOOL_CONSUMER_INSTANCE_GUID,
    display_name=Faker("name"),
)
