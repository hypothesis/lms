from factory import Faker, fuzzy, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

HubSpotCompany = make_factory(
    models.HubSpotCompany,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    name=Faker("company"),
    hubspot_id=fuzzy.FuzzyInteger(1, 9999999999),
)
