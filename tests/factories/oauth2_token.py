from datetime import datetime

from factory import SubFactory, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.application_instance import ApplicationInstance
from tests.factories.attributes import ACCESS_TOKEN, REFRESH_TOKEN, USER_ID

OAuth2Token = make_factory(
    models.OAuth2Token,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    user_id=USER_ID,
    application_instance=SubFactory(ApplicationInstance),
    access_token=ACCESS_TOKEN,
    # This is intentionally an "old" time and not a token that was very recently
    # received.
    received_at=datetime(2023, 12, 1),
    refresh_token=REFRESH_TOKEN,
)
