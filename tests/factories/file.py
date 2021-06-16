from factory import Faker, make_factory
from factory.alchemy import SQLAlchemyModelFactory

from lms import models

File = make_factory(
    models.File,
    FACTORY_CLASS=SQLAlchemyModelFactory,
    type=Faker("random_element", elements=["canvas_file", "decoy_type"]),
    lms_id=Faker("hexify", text="^" * 40),
    course_id=Faker("hexify", text="^" * 40),
    name=Faker("file_name", extension="pdf"),
    size=Faker("numerify", text="#"),
)
