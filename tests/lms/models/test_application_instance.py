from lms.models import ApplicationInstance


class TestApplicationInstance(object):
    def test_it_persists_application_instance(self, db_session):
        initial_count = db_session.query(ApplicationInstance).count()
        instance = ApplicationInstance(
            consumer_key='TEST_CONSUMER_KEY',
            shared_secret='TEST_SHARED_SECRET',
            lms_url='TEST_LMS_URL',
        )
        db_session.add(instance)
        new_count = db_session.query(ApplicationInstance).count()
        assert new_count == initial_count + 1
