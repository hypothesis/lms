from unittest.mock import sentinel

import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance, ApplicationSettings, ReusedConsumerKey
from tests import factories


class TestApplicationInstance:
    def test_it_persists_application_instance(self, db_session):
        initial_count = db_session.query(ApplicationInstance).count()

        factories.ApplicationInstance()

        new_count = db_session.query(ApplicationInstance).count()
        assert new_count == initial_count + 1

    def test_provisioning_defaults_to_True(self, application_instance, db_session):
        db_session.flush()

        assert application_instance.provisioning is True

    def test_provisioning_can_be_disabled(self, application_instance, db_session):
        application_instance.provisioning = False
        db_session.flush()

        assert not application_instance.provisioning

    def test_provisioning_is_not_nullable(self, db_session, application_instance):
        application_instance.provisioning = None

        db_session.flush()

        assert application_instance.provisioning is not None

    def test_settings_can_be_retrieved(self, application_instance):
        application_instance.settings = {"group": {"key": "value"}}

        assert application_instance.settings.get("group", "key") == "value"

    def test_can_update_settings(self, application_instance):
        application_instance.settings = {"group": {"key": "value"}}

        application_instance.settings.set("group", "key", "new_value")

        assert application_instance.settings["group"]["key"] == "new_value"

    def test_consumer_key_cant_be_null(self, db_session, application_instance):
        application_instance.consumer_key = None

        with pytest.raises(IntegrityError, match="consumer_key"):
            db_session.flush()

    def test_shared_secret_cant_be_null(self, db_session, application_instance):
        application_instance.shared_secret = None

        with pytest.raises(IntegrityError, match="shared_secret"):
            db_session.flush()

    def test_lms_url_cant_be_null(self, db_session, application_instance):
        application_instance.lms_url = None

        with pytest.raises(IntegrityError, match="lms_url"):
            db_session.flush()

    def test_requesters_email_cant_be_null(self, db_session, application_instance):
        application_instance.requesters_email = None

        with pytest.raises(IntegrityError, match="requesters_email"):
            db_session.flush()

    def test_lms_host(self, application_instance):
        application_instance.lms_url = "https://example.com/lms/"

        assert application_instance.lms_host() == "example.com"

    @pytest.mark.parametrize("lms_url", ["", "foo", "https://example[.com/foo"])
    def test_lms_host_raises_ValueError(self, application_instance, lms_url):
        application_instance.lms_url = lms_url

        with pytest.raises(ValueError):
            application_instance.lms_host()

    def test_decrypted_developer_secret_returns_the_decrypted_developer_secret(
        self, application_instance, aes_service
    ):
        application_instance.developer_secret = sentinel.developer_secret
        application_instance.aes_cipher_iv = sentinel.aes_cipher_iv

        developer_secret = application_instance.decrypted_developer_secret(aes_service)

        aes_service.decrypt.assert_called_once_with(
            application_instance.aes_cipher_iv, application_instance.developer_secret
        )
        assert developer_secret == aes_service.decrypt.return_value

    def test_decrypted_developer_secret_returns_None_if_ApplicationInstance_has_no_developer_secret(
        self, application_instance, aes_service
    ):
        assert application_instance.decrypted_developer_secret(aes_service) is None

    def test_update_lms_data(self, application_instance, lms_data):
        lms_data["tool_consumer_instance_guid"] = "GUID"
        application_instance.update_lms_data(lms_data)

        for k, v in lms_data.items():
            assert getattr(application_instance, k) == v

    def test_update_lms_data_no_guid_doesnt_change_values(
        self, application_instance, lms_data
    ):
        application_instance.update_lms_data(lms_data)

        assert application_instance.tool_consumer_instance_guid is None
        assert application_instance.tool_consumer_info_product_family_code is None

    def test_update_lms_data_existing_guid(self, application_instance, lms_data):
        application_instance.tool_consumer_instance_guid = "EXISTING_GUID"
        lms_data["tool_consumer_instance_guid"] = "NEW GUID"

        with pytest.raises(ReusedConsumerKey):
            application_instance.update_lms_data(lms_data)

        assert application_instance.tool_consumer_instance_guid == "EXISTING_GUID"

    @pytest.mark.parametrize(
        "value,expected",
        [
            ("BlackboardLearn", ApplicationInstance.Product.BLACKBOARD),
            ("canvas", ApplicationInstance.Product.CANVAS),
            ("moodle", ApplicationInstance.Product.MOODLE),
            ("desire2learn", ApplicationInstance.Product.D2L),
            ("BlackbaudK12", ApplicationInstance.Product.BLACKBAUD),
            ("schoology", ApplicationInstance.Product.SCHOOLOGY),
            ("sakai", ApplicationInstance.Product.SAKAI),
            ("wut", ApplicationInstance.Product.UNKNOWN),
        ],
    )
    def test_product(self, value, expected, application_instance):
        application_instance.tool_consumer_info_product_family_code = value

        assert application_instance.product == expected

    @pytest.fixture
    def application_instance(self):
        """Return an ApplicationInstance with minimal required attributes."""
        return factories.ApplicationInstance()

    @pytest.fixture
    def lms_data(self):
        return {
            "tool_consumer_info_product_family_code": "FAMILY",
            "tool_consumer_instance_description": "DESCRIPTION",
            "tool_consumer_instance_url": "URL",
            "tool_consumer_instance_name": "NAME",
        }


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
