import pytest
from Cryptodome import Random
from Cryptodome.Cipher import AES
from sqlalchemy.exc import IntegrityError

from lms.models import ApplicationInstance, ApplicationSettings
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

    def test_settings_defaults_to_None(self, application_instance):
        settings = application_instance.settings

        assert settings is None

    def test_consumer_key_default(self, application_instance):
        consumer_key = application_instance.consumer_key

        assert consumer_key.startswith("Hypothesis")

    def test_shared_secret_default(self, application_instance):
        shared_secret = application_instance.shared_secret

        assert len(shared_secret) == 32 * 2  # n bytes * two chars per byte

    def test_settings_can_be_retrieved(self, application_instance):
        application_instance.settings = {"group": {"key": "value"}}

        assert application_instance.settings.get("group", "key") == "value"

    def test_can_update_settings(self, application_instance):
        application_instance.settings = {"group": {"key": "value"}}

        application_instance.settings.set("group", "key", "new_value")

        assert application_instance.settings["group"]["key"] == "new_value"

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
        self, application_instance, pyramid_request
    ):
        aes_secret = pyramid_request.registry.settings["aes_secret"]
        application_instance.aes_cipher_iv = Random.new().read(AES.block_size)
        application_instance.developer_secret = AES.new(
            aes_secret, AES.MODE_CFB, application_instance.aes_cipher_iv
        ).encrypt(b"TEST_DEVELOPER_SECRET")

        assert (
            application_instance.decrypted_developer_secret(aes_secret)
            == b"TEST_DEVELOPER_SECRET"
        )

    def test_decrypted_developer_secret_returns_None_if_ApplicationInstance_has_no_developer_secret(
        self, application_instance, pyramid_request
    ):
        aes_secret = pyramid_request.registry.settings["aes_secret"]

        assert application_instance.decrypted_developer_secret(aes_secret) is None

    def test_encrypt_developer_secret_with_no_input(self, application_instance):
        application_instance.encrypt_developer_secret(None, "not none", "aes_secret")

        assert (
            application_instance.developer_secret
            == application_instance.developer_key
            is None
        )

    def test_encrypt_developer_secret(
        self, application_instance, pyramid_request, aes, random
    ):
        aes_secret = pyramid_request.registry.settings["aes_secret"]

        application_instance.encrypt_developer_secret(
            "TEST_DEVELOPER_KEY", "TEST_DEVELOPER_SECRET", aes_secret
        )

        random.new.return_value.read.assert_called_once()
        assert application_instance.developer_key == "TEST_DEVELOPER_KEY"
        assert (
            application_instance.developer_secret
            == aes.new.return_value.encrypt.return_value
        )
        assert (
            application_instance.aes_cipher_iv
            == random.new.return_value.read.return_value
        )

    def test_encrypt_developer_secret_with_cipher(
        self, application_instance, pyramid_request, aes
    ):
        aes_secret = pyramid_request.registry.settings["aes_secret"]

        application_instance.aes_cipher_iv = Random.new().read(AES.block_size)
        application_instance.encrypt_developer_secret(
            "TEST_DEVELOPER_KEY", "TEST_DEVELOPER_SECRET", aes_secret
        )

        assert application_instance.developer_key == "TEST_DEVELOPER_KEY"
        assert (
            application_instance.developer_secret
            == aes.new.return_value.encrypt.return_value
        )

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

        application_instance.update_lms_data(lms_data)

        assert application_instance.tool_consumer_instance_guid == "EXISTING_GUID"

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

    @pytest.fixture
    def aes(self, patch):
        return patch("lms.models.application_instance.AES")

    @pytest.fixture
    def random(self, patch):
        return patch("lms.models.application_instance.Random")


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
