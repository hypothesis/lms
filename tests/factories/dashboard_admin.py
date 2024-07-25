from factory import make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

DashboardAdmin = make_factory(
    models.DashboardAdmin,
    FACTORY_CLASS=SQLAlchemyModelFactory,
)
