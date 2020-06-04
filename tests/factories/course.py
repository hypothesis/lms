import factory

from lms import models

Course = factory.make_factory(  # pylint:disable=invalid-name
    models.Course,
    consumer_key=factory.Faker("hexify", text="^" * 40),
    authority_provided_id=factory.Faker("hexify", text="^" * 40),
    _settings=factory.lazy_attribute(lambda o: {}),
)
