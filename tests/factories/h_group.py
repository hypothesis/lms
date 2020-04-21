from factory import Faker, Sequence, make_factory

from lms import models

HGroup = make_factory(  # pylint:disable=invalid-name
    models.HGroup,
    name=Sequence(lambda n: f"Test Group {n}"),
    authority_provided_id=Faker("hexify", text="^" * 40),
)
