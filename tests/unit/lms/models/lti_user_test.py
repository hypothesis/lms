import pytest

from tests import factories


class TestLTIUser:
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

        assert lti_user.is_instructor == is_instructor  # pylint:disable=no-member

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
