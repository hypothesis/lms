from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories._attributes import OAUTH_CONSUMER_KEY, SHARED_SECRET

ApplicationInstance = make_factory(  # pylint:disable=invalid-name
    models.ApplicationInstance,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    consumer_key=OAUTH_CONSUMER_KEY,
    shared_secret=SHARED_SECRET,
    lms_url=Faker("uri"),
    requesters_email=Faker("email"),
)
