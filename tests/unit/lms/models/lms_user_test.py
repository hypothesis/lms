from tests import factories


class TestLMSUser:
    def test_user_id(self):
        lms_user = factories.LMSUser()

        assert lms_user.lti_user_id
        assert lms_user.lti_user_id == lms_user.user_id

    def test_application_instance(self, application_instance, db_session):
        lms_user = factories.LMSUser()
        factories.LMSUserApplicationInstance(
            lms_user=lms_user, application_instance=application_instance
        )
        db_session.flush()

        assert lms_user.application_instance == application_instance
