from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

LTIRegistration = make_factory(
    models.LTIRegistration,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    issuer=Faker("hostname"),
    client_id=Faker("hexify", text="^" * 40),
    auth_login_url=Faker("uri"),
    key_set_url=Faker("uri"),
    token_url=Faker("uri"),
)
