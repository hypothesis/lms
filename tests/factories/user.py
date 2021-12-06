from factory import Faker, SubFactory, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.application_instance import ApplicationInstance
from tests.factories.attributes import H_USERID, USER_ID

User = make_factory(
    models.User,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    application_instance=SubFactory(ApplicationInstance),
    user_id=USER_ID,
    roles=Faker("random_element", elements=["Learner", "Instructor"]),
    h_userid=H_USERID,
)
