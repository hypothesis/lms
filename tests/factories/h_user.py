import factory

from lms import models

HUser = factory.make_factory(  # pylint:disable=invalid-name
    models.HUser,
    username=factory.Faker("hexify", text="^" * 30),
    display_name=factory.Faker("name"),
    provider=factory.Faker("hexify", text="^" * 40),
    provider_unique_id=factory.Faker("hexify", text="^" * 40),
)
