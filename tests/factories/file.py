from factory import Faker, Sequence, SubFactory, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from tests.factories.application_instance import ApplicationInstance

File = make_factory(
    models.File,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    application_instance=SubFactory(ApplicationInstance),
    type="canvas_file",
    lms_id=Sequence(lambda n: f"{n}"),
    course_id=Faker("numerify", text="course_####"),
    name=Faker("word"),
    size=Faker("random_int"),
)
