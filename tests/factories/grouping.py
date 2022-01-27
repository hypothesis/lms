import factory
from factory.alchemy import SQLAlchemyModelFactory

from lms.models import BlackboardGroup, CanvasGroup, CanvasSection, Course
from tests.factories import ApplicationInstance


def _grouping_factory(model_class, lms_name, parent=None):
    return factory.make_factory(
        model_class,
        FACTORY_CLASS=SQLAlchemyModelFactory,
        application_instance=factory.SubFactory(ApplicationInstance),
        authority_provided_id=factory.Faker("hexify", text="^" * 40),
        lms_id=factory.Faker("hexify", text="^" * 40),
        lms_name=lms_name,
        parent=parent,
    )


def _child_grouping_factory(model_class, lms_name):
    return _grouping_factory(model_class, lms_name, parent=factory.SubFactory(Course))


Course = _grouping_factory(Course, lms_name=factory.Sequence(lambda n: f"Course {n}"))


BlackboardGroup = _child_grouping_factory(
    BlackboardGroup, lms_name=factory.Sequence(lambda n: f"Blackboard Group {n}")
)


CanvasSection = _child_grouping_factory(
    CanvasSection, lms_name=factory.Sequence(lambda n: f"Canvas Section {n}")
)


CanvasGroup = _child_grouping_factory(
    CanvasGroup, lms_name=factory.Sequence(lambda n: f"Canvas Group {n}")
)
