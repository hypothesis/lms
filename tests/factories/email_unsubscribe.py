from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.attributes import H_USERID

EmailUnsubscribe = make_factory(
    models.EmailUnsubscribe,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    tag=Faker("word"),
    h_userid=H_USERID,
)
