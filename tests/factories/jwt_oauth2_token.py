from factory import SubFactory, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.attributes import ACCESS_TOKEN
from tests.factories.lti_registration import LTIRegistration

JWTOAuth2Token = make_factory(
    models.JWTOAuth2Token,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    lti_registration=SubFactory(LTIRegistration),
    access_token=ACCESS_TOKEN,
)
