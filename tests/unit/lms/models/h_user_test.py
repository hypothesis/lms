from lms.models import HUser
from tests import factories


class TestHUser:
    def test_userid(self):
        h_user = factories.HUser(username="test_username")

        assert h_user.userid("test_authority") == "acct:test_username@test_authority"

    def test_from_lti_user(self):
        lti_user = factories.LTIUser(
            tool_consumer_instance_guid="test_tool_consumer_instance_guid",
            user_id="test_user_id",
        )

        assert HUser.from_lti_user(lti_user) == HUser(
            username="16aa3b3e92cdfa53e5996d138a7013",
            display_name=lti_user.display_name,
            provider=lti_user.tool_consumer_instance_guid,
            provider_unique_id=lti_user.user_id,
        )
