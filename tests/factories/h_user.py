import factory

from lms import models

HUser = factory.make_factory(  # pylint:disable=invalid-name
    models.HUser,
    authority="lms.hypothes.is",
    username=factory.Faker("hexify", text="^" * 30),
    display_name=factory.Faker("name"),
)
