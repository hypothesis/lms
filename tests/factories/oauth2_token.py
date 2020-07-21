from factory import SubFactory, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.application_instance import ApplicationInstance
from tests.factories.attributes import ACCESS_TOKEN, REFRESH_TOKEN, USER_ID

OAuth2Token = make_factory(  # pylint:disable=invalid-name
    models.OAuth2Token,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    user_id=USER_ID,
    application_instance=SubFactory(ApplicationInstance),
    access_token=ACCESS_TOKEN,
    refresh_token=REFRESH_TOKEN,
)
