import pytest

from lms.models import HUser
from tests import factories


class TestHUser:
    def test_userid(self):
        h_user = factories.HUser(username="test_username")

        assert h_user.userid("test_authority") == "acct:test_username@test_authority"

    def test_from_lti_user(self, hashed_id):
        lti_user = factories.LTIUser(
            tool_consumer_instance_guid="test_tool_consumer_instance_guid",
            user_id="test_user_id",
        )

        h_user = HUser.from_lti_user(lti_user)

        hashed_id.assert_called_once_with(h_user.provider, h_user.provider_unique_id)

        assert h_user == HUser(
            username=hashed_id.return_value[:30],
            display_name=lti_user.display_name,
            provider=lti_user.tool_consumer_instance_guid,
            provider_unique_id=lti_user.user_id,
        )

    @pytest.fixture
    def hashed_id(self, patch):
        hashed_id = patch("lms.models.h_user.hashed_id")
        hashed_id.return_value = "x" * 30 + "1234567890"

        return hashed_id
