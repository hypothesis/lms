import factory

from lms import models
from tests.factories._attributes import H_DISPLAY_NAME, H_USERNAME

HUser = factory.make_factory(  # pylint:disable=invalid-name
    models.HUser,
    username=H_USERNAME,
    display_name=H_DISPLAY_NAME,
    provider=factory.Faker("hexify", text="^" * 40),
    provider_unique_id=factory.Faker("hexify", text="^" * 40),
)
