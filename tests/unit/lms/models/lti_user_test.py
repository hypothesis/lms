import pytest

from lms.models import display_name
from lms.models.lti_role import LTIRole, RoleScope, RoleType
from tests import factories


class TestLTIUser:
    def test_h_user(self, HUser):
        lti_user = factories.LTIUser()

        h_user = lti_user.h_user

        HUser.from_lti_user.assert_called_once_with(lti_user)
        assert h_user == HUser.from_lti_user.return_value

    @pytest.mark.parametrize(
        "role,is_instructor",
        [
            (LTIRole(scope=RoleScope.COURSE, type=RoleType.ADMIN), True),
            (LTIRole(scope=RoleScope.INSTITUTION, type=RoleType.ADMIN), True),
            (LTIRole(scope=RoleScope.COURSE, type=RoleType.INSTRUCTOR), True),
            (
                LTIRole(scope=RoleScope.INSTITUTION, type=RoleType.INSTRUCTOR),
                False,
            ),
            (LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER), False),
        ],
    )
    def test_is_instructor(self, role, is_instructor):
        lti_user = factories.LTIUser(lti_roles=[role])

        assert lti_user.is_instructor == is_instructor

    @pytest.mark.parametrize(
        "role,is_learner",
        [
            (LTIRole(scope=RoleScope.COURSE, type=RoleType.ADMIN), False),
            (LTIRole(scope=RoleScope.COURSE, type=RoleType.INSTRUCTOR), False),
            (LTIRole(scope=RoleScope.INSTITUTION, type=RoleType.LEARNER), False),
            (LTIRole(scope=RoleScope.COURSE, type=RoleType.LEARNER), True),
        ],
    )
    def test_is_learner(self, role, is_learner):
        lti_user = factories.LTIUser(lti_roles=[role])

        assert lti_user.is_learner == is_learner

    @pytest.mark.parametrize(
        "role,is_admin",
        [
            (LTIRole(scope=RoleScope.COURSE, type=RoleType.ADMIN), True),
            (LTIRole(scope=RoleScope.INSTITUTION, type=RoleType.ADMIN), True),
            (LTIRole(scope=RoleScope.INSTITUTION, type=RoleType.INSTRUCTOR), False),
        ],
    )
    def test_is_admin(self, role, is_admin):
        lti_user = factories.LTIUser(lti_roles=[role])

        assert lti_user.is_admin == is_admin


@pytest.mark.parametrize(
    "given_name,family_name,full_name,expected_display_name",
    [
        # It returns the full name if there is one.
        ("given", "family", "full", "full"),
        # If there's no full name it concatenates given and family names.
        ("given", "family", "", "given family"),
        ("given", "family", " ", "given family"),
        # If there's no full name or given name it uses just the family name.
        ("", "family", " ", "family"),
        # If there's no full name or family name it uses just the given name.
        ("given", "", "", "given"),
        ("given", " ", " ", "given"),
        # If there's nothing else it just returns "Anonymous".
        ("", "", "", "Anonymous"),
        (" ", " ", " ", "Anonymous"),
        # Test white space stripping
        ("", "", " full ", "full"),
        ("  given ", "", "", "given"),
        ("", "  family ", "", "family"),
        ("  given  ", "  family  ", "", "given family"),
        # Test truncation
        ("", "", "x" * 100, "x" * 29 + "…"),
        ("x" * 100, "", "", "x" * 29 + "…"),
        ("", "x" * 100, "", "x" * 29 + "…"),
        ("given" * 3, "family" * 3, "", "givengivengiven familyfamilyf…"),
    ],
)
def test_display_name(given_name, family_name, full_name, expected_display_name):
    display_name_ = display_name(given_name, family_name, full_name)

    assert display_name_ == expected_display_name


@pytest.fixture(autouse=True)
def HUser(patch):
    return patch("lms.models.lti_user.HUser")
