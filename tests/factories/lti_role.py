import factory
from factory import Faker, Sequence
from factory.alchemy import SQLAlchemyModelFactory

from lms import models
from lms.models.lti_role import RoleScope, RoleType


class LTIRole(SQLAlchemyModelFactory):
    class Meta:
        model = models.LTIRole

        exclude = ("primary_role", "sub_role")

    primary_role = Faker(
        "random_element",
        elements=[
            "http://purl.imsglobal.org/vocab/lis/v2/membership/Administrator",
            "http://purl.imsglobal.org/vocab/lis/v2/membership/ContentDeveloper",
            "http://purl.imsglobal.org/vocab/lis/v2/membership/Learner",
            "http://purl.imsglobal.org/vocab/lis/v2/membership/Mentor",
            "http://purl.imsglobal.org/vocab/lis/v2/membership/Manager",
            "http://purl.imsglobal.org/vocab/lis/v2/membership/Office",
        ],
    )
    sub_role = Sequence(lambda n: f"SubRole{n}")

    # We want the value to be random, but it must also be guaranteed unique
    value = factory.LazyAttribute(lambda o: f"{o.primary_role}#{o.sub_role}")


class LTIRoleOverride(SQLAlchemyModelFactory):
    class Meta:
        model = models.LTIRoleOverride

    type = Faker("random_element", elements=list(RoleType))
    scope = Faker("random_element", elements=list(RoleScope))
