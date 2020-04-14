from tests import factories


class TestHUser:
    def test_userid(self):
        h_user = factories.HUser(username="test_username", authority="test_authority")

        assert h_user.userid == "acct:test_username@test_authority"
