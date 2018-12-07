from lms.models import ApplicationInstance


class TestApplicationInstance:
    def test_it_persists_application_instance(self, db_session):
        initial_count = db_session.query(ApplicationInstance).count()
        instance = ApplicationInstance(
            consumer_key="TEST_CONSUMER_KEY",
            shared_secret="TEST_SHARED_SECRET",
            lms_url="TEST_LMS_URL",
        )
        db_session.add(instance)
        new_count = db_session.query(ApplicationInstance).count()
        assert new_count == initial_count + 1

    def test_provisioning_defaults_to_True(self, db_session):
        application_instance = ApplicationInstance()
        db_session.add(application_instance)

        db_session.flush()

        assert application_instance.provisioning is True

    def test_provisioning_can_be_disabled(self, db_session):
        application_instance = ApplicationInstance()
        application_instance.provisioning = False
        db_session.add(application_instance)
        db_session.flush()

        assert application_instance.provisioning is False

    def test_provisioning_is_not_nullable(self, db_session):
        application_instance = ApplicationInstance()
        application_instance.provisioning = None
        db_session.add(application_instance)

        db_session.flush()

        assert application_instance.provisioning is not None
