from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

RSAKey = make_factory(
    models.RSAKey, FACTORY_CLASS=SQLAlchemyModelFactory, public_key="{}"
)
