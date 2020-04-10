from unittest import mock

import pytest

from lms.models import LTIUser


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
        lti_user = LTIUser(
            mock.sentinel.userid, mock.sentinel.oauth_consumer_key, roles
        )

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
        lti_user = LTIUser(
            mock.sentinel.userid, mock.sentinel.oauth_consumer_key, roles
        )

        assert lti_user.is_learner == is_learner
