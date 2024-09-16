from factory import Faker, SubFactory, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from lms.models.grading_sync import AutoGradingSyncStatus
from tests.factories.lms_user import LMSUser


class GradingSync(SQLAlchemyModelFactory):
    class Meta:
        model = models.GradingSync

    created_by = SubFactory(LMSUser)
    status = Faker("random_element", elements=list(AutoGradingSyncStatus))


GradingSyncGrade = make_factory(
    models.GradingSyncGrade, FACTORY_CLASS=SQLAlchemyModelFactory
)
