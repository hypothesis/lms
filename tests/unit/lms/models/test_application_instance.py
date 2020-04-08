import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance


class TestApplicationInstance:
    def test_it_persists_application_instance(self, db_session, application_instance):
        initial_count = db_session.query(ApplicationInstance).count()
        db_session.add(application_instance)
        new_count = db_session.query(ApplicationInstance).count()
        assert new_count == initial_count + 1

    def test_provisioning_defaults_to_True(self, db_session, application_instance):
        db_session.add(application_instance)

        db_session.flush()

        assert application_instance.provisioning is True

    def test_provisioning_can_be_disabled(self, db_session, application_instance):
        application_instance.provisioning = False
        db_session.add(application_instance)
        db_session.flush()

        assert not application_instance.provisioning

    def test_provisioning_is_not_nullable(self, db_session, application_instance):
        application_instance.provisioning = None
        db_session.add(application_instance)

        db_session.flush()

        assert application_instance.provisioning is not None

    def test_consumer_key_cant_be_null(self, db_session, application_instance):
        application_instance.consumer_key = None
        db_session.add(application_instance)

        with pytest.raises(IntegrityError, match="consumer_key"):
            db_session.flush()

    def test_shared_secret_cant_be_null(self, db_session, application_instance):
        application_instance.shared_secret = None
        db_session.add(application_instance)

        with pytest.raises(IntegrityError, match="shared_secret"):
            db_session.flush()

    def test_lms_url_cant_be_null(self, db_session, application_instance):
        application_instance.lms_url = None
        db_session.add(application_instance)

        with pytest.raises(IntegrityError, match="lms_url"):
            db_session.flush()

    def test_requesters_email_cant_be_null(self, db_session, application_instance):
        application_instance.requesters_email = None
        db_session.add(application_instance)

        with pytest.raises(IntegrityError, match="requesters_email"):
            db_session.flush()

    def test_get_returns_the_matching_ApplicationInstance(
        self, db_session, application_instance
    ):
        db_session.add(application_instance)

        assert (
            ApplicationInstance.get(db_session, application_instance.consumer_key)
            == application_instance
        )

    @pytest.mark.usefixtures("application_instance")
    def test_get_returns_None_if_theres_no_matching_ApplicationInstance(
        self, db_session
    ):
        assert ApplicationInstance.get(db_session, "unknown_consumer_key") is None

    @pytest.fixture
    def application_instance(self):
        """Return an ApplicationInstance with minimal required attributes."""
        return ApplicationInstance(
            consumer_key="TEST_CONSUMER_KEY",
            shared_secret="TEST_SHARED_SECRET",
            lms_url="TEST_LMS_URL",
            requesters_email="TEST_EMAIL",
        )
