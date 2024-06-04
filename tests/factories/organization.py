import base64
import uuid

from factory import Faker, LazyAttribute, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

Organization = make_factory(
    models.Organization,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    name=Faker("company"),
    public_id=LazyAttribute(
        lambda _: "us.lms.org."
        + base64.urlsafe_b64encode(uuid.uuid4().bytes).decode("ascii").rstrip("=")
    ),
    settings={},
)
