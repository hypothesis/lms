from factory import Faker, make_factory

from lms import models
from tests.factories._attributes import OAUTH_CONSUMER_KEY, USER_ID

OAuth2Token = make_factory(  # pylint:disable=invalid-name
    models.OAuth2Token,
    user_id=USER_ID,
    consumer_key=OAUTH_CONSUMER_KEY,
    access_token=Faker("hexify", text="^" * 32),
    refresh_token=Faker("hexify", text="^" * 32),
)
