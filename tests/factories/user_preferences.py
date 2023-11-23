from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.attributes import H_USERID

UserPreferences = make_factory(
    models.UserPreferences, FACTORY_CLASS=SQLAlchemyModelFactory, h_userid=H_USERID
)
