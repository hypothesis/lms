from factory import Faker, make_factory

from lms import models
from tests.factories.attributes import OAUTH_CONSUMER_KEY, USER_ID

LTIUser = make_factory(  # pylint:disable=invalid-name
    models.LTIUser,
    user_id=USER_ID,
    oauth_consumer_key=OAUTH_CONSUMER_KEY,
    roles=Faker("random_element", elements=["Learner", "Instructor"]),
    tool_consumer_instance_guid=Faker("hexify", text="^" * 40),
    display_name=Faker("name"),
)
