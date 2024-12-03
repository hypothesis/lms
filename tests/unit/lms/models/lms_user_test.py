from tests import factories


class TestLMSUser:
    def test_user_id(self):
        lms_user = factories.LMSUser()

        assert lms_user.lti_user_id
        assert lms_user.lti_user_id == lms_user.user_id
