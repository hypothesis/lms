from factory import Faker, make_factory

from lms import models

LTIUser = make_factory(  # pylint:disable=invalid-name
    models.LTIUser,
    user_id=Faker("hexify", text="^" * 40),
    oauth_consumer_key=Faker("hexify", text="Hypothesis" + "^" * 32),
    roles=Faker("random_element", elements=["Learner", "Instructor"]),
    tool_consumer_instance_guid=Faker("hexify", text="^" * 40),
    display_name=Faker("name"),
)
