from factory import Faker, Sequence, make_factory

from lms import models

HGroup = make_factory(
    models.HGroup,
    _name=Sequence(lambda n: f"Test Group {n}"),
    authority_provided_id=Faker("hexify", text="^" * 40),
    type=Faker("random_element", elements=["course_group", "section_group"]),
)
