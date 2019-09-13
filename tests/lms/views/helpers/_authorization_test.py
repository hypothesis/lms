import pytest

from lms.views.helpers import is_instructor
from lms.values import LTIUser


class TestIsInstructor:
    @pytest.mark.parametrize(
        "roles",
        [
            "instructor",
            "urn:lti:role:ims/lis/Instructor",
            "teachingassistant",
            "administrator",
            "urn:lti:role:ims/lis/Learner,urn:lti:role:ims/lis/Instructor",
            "urn:lti:role:ims/lis/Instructor,instructor,student",
        ],
    )
    def test_it_returns_true_if_valid_instructor_role_in_roles(
        self, pyramid_request, roles
    ):
        pyramid_request.lti_user = LTIUser(
            "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", roles
        )

        assert is_instructor(pyramid_request) is True

    @pytest.mark.parametrize(
        "roles",
        [
            "",
            "student",
            "urn:lti:role:ims/lis/Professor",
            "urn:lti:role:ims/lis/Learner",
        ],
    )
    def test_it_returns_false_if_no_valid_instructor_role_in_roles(
        self, pyramid_request, roles
    ):
        pyramid_request.lti_user = LTIUser(
            "TEST_USER_ID", "TEST_OAUTH_CONSUMER_KEY", roles
        )

        assert is_instructor(pyramid_request) is False
