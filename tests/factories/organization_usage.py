from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

OrganizationUsageReport = make_factory(
    models.OrganizationUsageReport,
    FACTORY_CLASS=SQLAlchemyModelFactory,
)
