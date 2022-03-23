import pytest

from lms.models import LTIUser, display_name
from tests import factories


class TestLTIUser:
    def test_h_user(self, HUser):
        lti_user = factories.LTIUser()

        h_user = lti_user.h_user

        HUser.from_lti_user.assert_called_once_with(lti_user)
        assert h_user == HUser.from_lti_user.return_value

    @pytest.mark.parametrize(
        "roles,is_instructor",
        [
            ("Administrator", True),
            ("Instructor", True),
            ("TeachingAssistant", True),
            ("Learner", False),
        ],
    )
    def test_is_instructor(self, roles, is_instructor):
        lti_user = factories.LTIUser(roles=roles)

        assert lti_user.is_instructor == is_instructor

    @pytest.mark.parametrize(
        "roles,is_learner",
        [
            ("Administrator", False),
            ("Instructor", False),
            ("TeachingAssistant", False),
            ("Learner", True),
        ],
    )
    def test_is_learner(self, roles, is_learner):
        lti_user = factories.LTIUser(roles=roles)

        assert lti_user.is_learner == is_learner

    def test_from_auth_params(self, application_instance, auth_params):
        lti_user = LTIUser.from_auth_params(application_instance, auth_params)

        assert lti_user.user_id == auth_params["user_id"]
        assert lti_user.roles == auth_params["roles"]
        assert (
            lti_user.tool_consumer_instance_guid
            == auth_params["tool_consumer_instance_guid"]
        )
        assert lti_user.email == auth_params["lis_person_contact_email_primary"]
        assert lti_user.display_name == display_name(
            auth_params["lis_person_name_given"],
            auth_params["lis_person_name_family"],
            auth_params["lis_person_name_full"],
        )
        assert lti_user.application_instance_id == application_instance.id

    @pytest.fixture
    def auth_params(self):
        return {
            "user_id": "USER_ID",
            "roles": "ROLES",
            "tool_consumer_instance_guid": "TOOL_CONSUMER_INSTANCE_GUID",
            "lis_person_name_given": "LIS_PERSON_NAME_GIVEN",
            "lis_person_name_family": "LIS_PERSON_NAME_FAMILY",
            "lis_person_name_full": "LIS_PERSON_NAME_FULL",
            "lis_person_contact_email_primary": "LIS_PERSON_CONTACT_EMAIL_PRIMARY",
        }


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
