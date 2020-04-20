from tests import factories


class TestHUser:
    def test_userid(self):
        h_user = factories.HUser(username="test_username")

        assert h_user.userid("test_authority") == "acct:test_username@test_authority"
