import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance, ApplicationSettings

# pylint: disable=protected-access


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

    def test_settings_defaults_to_an_empty_dict(self, application_instance):
        settings = application_instance.settings

        assert isinstance(settings, ApplicationSettings)
        assert settings.data == {}

    def test_settings_can_be_retrieved(self, application_instance):
        application_instance._settings = {"group": {"key": "value"}}

        assert application_instance.settings.get("group", "key") == "value"

    def test_can_update_settings(self, application_instance):
        application_instance._settings = {"group": {"key": "value"}}

        application_instance.settings.set("group", "key", "new_value")

        assert application_instance._settings["group"]["key"] == "new_value"

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
            ApplicationInstance.get_by_consumer_key(
                db_session, application_instance.consumer_key
            )
            == application_instance
        )

    @pytest.mark.usefixtures("application_instance")
    def test_get_returns_None_if_theres_no_matching_ApplicationInstance(
        self, db_session
    ):
        assert (
            ApplicationInstance.get_by_consumer_key(db_session, "unknown_consumer_key")
            is None
        )

    @pytest.fixture
    def application_instance(self):
        """Return an ApplicationInstance with minimal required attributes."""
        return ApplicationInstance(
            consumer_key="TEST_CONSUMER_KEY",
            shared_secret="TEST_SHARED_SECRET",
            lms_url="TEST_LMS_URL",
            requesters_email="TEST_EMAIL",
        )


class TestApplicationSettings:
    @pytest.mark.parametrize(
        "group,key,expected_value",
        (
            ("group", "key", "old_value"),
            ("NEW", "key", None),
            ("group", "NEW", None),
            ("NEW", "NEW", None),
        ),
    )
    def test_settings_can_be_retrieved(self, settings, group, key, expected_value):
        assert settings.get(group, key) == expected_value

    @pytest.mark.parametrize(
        "group,key",
        (("group", "key"), ("NEW", "key"), ("group", "NEW"), ("NEW", "NEW")),
    )
    def test_can_update_settings(self, settings, group, key):
        settings.set(group, key, "new_value")

        assert settings.get(group, key) == "new_value"

    @pytest.fixture
    def settings(self):
        return ApplicationSettings({"group": {"key": "old_value"}})
