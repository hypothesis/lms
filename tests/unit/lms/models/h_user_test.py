from lms.models import HUser


class TestHUser:
    def test_userid(self):
        h_user = HUser("test_authority", "test_username")

        assert h_user.userid == "acct:test_username@test_authority"
