from unittest import mock

import pytest

from lms.models import ApplicationInstance
from lms.models.application_instance import _build_aes_iv, _encrypt_oauth_secret
from lms.services import ConsumerKeyError
from lms.services.application_instance_getter import (
    application_instance_getter_service_factory,
)


class TestApplicationInstanceGetter:
    def test_developer_key_returns_the_developer_key(self, ai_getter):
        assert ai_getter.developer_key("TEST_CONSUMER_KEY") == "TEST_DEVELOPER_KEY"

    def test_developer_key_returns_None_if_ApplicationInstance_has_no_developer_key(
        self, ai_getter, test_application_instance
    ):
        test_application_instance.developer_key = None

        assert ai_getter.developer_key("TEST_CONSUMER_KEY") is None

    def test_developer_key_raises_if_consumer_key_unknown(self, ai_getter):
        with pytest.raises(ConsumerKeyError):
            ai_getter.developer_key("UNKNOWN_CONSUMER_KEY")

    def test_developer_secret_returns_the_decrypted_developer_secret(
        self, ai_getter, pyramid_request, test_application_instance
    ):
        test_application_instance.aes_cipher_iv = _build_aes_iv()
        test_application_instance.developer_secret = _encrypt_oauth_secret(
            b"TEST_DEVELOPER_SECRET",
            pyramid_request.registry.settings["aes_secret"],
            test_application_instance.aes_cipher_iv,
        )

        assert (
            ai_getter.developer_secret("TEST_CONSUMER_KEY") == b"TEST_DEVELOPER_SECRET"
        )

    def test_developer_secret_returns_None_if_ApplicationInstance_has_no_developer_secret(
        self, ai_getter
    ):
        assert ai_getter.developer_secret("TEST_CONSUMER_KEY") is None

    def test_developer_secret_raises_if_consumer_key_unknown(self, ai_getter):
        with pytest.raises(ConsumerKeyError):
            ai_getter.developer_secret("UNKNOWN_CONSUMER_KEY")

    def test_lms_url_returns_the_lms_url(self, ai_getter):
        assert ai_getter.lms_url("TEST_CONSUMER_KEY") == "TEST_LMS_URL"

    def test_lms_url_raises_if_consumer_key_unknown(self, ai_getter):
        with pytest.raises(ConsumerKeyError):
            ai_getter.lms_url("UNKNOWN_CONSUMER_KEY")

    @pytest.mark.parametrize("flag", [True, False])
    def test_provisioning_returns_the_provisioning_flag(
        self, ai_getter, flag, test_application_instance
    ):
        test_application_instance.provisioning = flag

        assert ai_getter.provisioning_enabled("TEST_CONSUMER_KEY") == flag

    def test_provisioning_returns_False_if_consumer_key_unknown(self, ai_getter):
        assert not ai_getter.provisioning_enabled("UNKNOWN_CONSUMER_KEY")

    def test_shared_secret_returns_the_shared_secret(self, ai_getter):
        assert ai_getter.shared_secret("TEST_CONSUMER_KEY") == "TEST_SHARED_SECRET"

    def test_shared_secret_raises_if_consumer_key_unknown(self, ai_getter):
        with pytest.raises(ConsumerKeyError):
            ai_getter.shared_secret("UNKNOWN_CONSUMER_KEY")

    @pytest.fixture
    def ai_getter(self, pyramid_request):
        return application_instance_getter_service_factory(
            mock.sentinel.context, pyramid_request
        )

    @pytest.fixture(autouse=True)
    def test_application_instance(self, pyramid_request):
        application_instance = ApplicationInstance(
            consumer_key="TEST_CONSUMER_KEY",
            developer_key="TEST_DEVELOPER_KEY",
            lms_url="TEST_LMS_URL",
            shared_secret="TEST_SHARED_SECRET",
            requesters_email="TEST_EMAIL",
        )
        pyramid_request.db.add(application_instance)
        return application_instance

    @pytest.fixture(autouse=True)
    def application_instances(self, pyramid_request):
        """Add some "noise" application instances."""
        # Add some "noise" application instances to the DB for every test, to
        # make the tests more realistic.
        application_instances = [
            ApplicationInstance(
                consumer_key="NOISE_CONSUMER_KEY_1",
                developer_key="NOISE_DEVELOPER_KEY_1",
                lms_url="NOISE_LMS_URL_1",
                shared_secret="NOISE_SHARED_SECRET_1",
                requesters_email="NOISE_EMAIL_1",
            ),
            ApplicationInstance(
                consumer_key="NOISE_CONSUMER_KEY_2",
                developer_key="NOISE_DEVELOPER_KEY_2",
                lms_url="NOISE_LMS_URL_2",
                shared_secret="NOISE_SHARED_SECRET_2",
                requesters_email="NOISE_EMAIL_2",
            ),
            ApplicationInstance(
                consumer_key="NOISE_CONSUMER_KEY_3",
                developer_key="NOISE_DEVELOPER_KEY_3",
                lms_url="NOISE_LMS_URL_3",
                shared_secret="NOISE_SHARED_SECRET_3",
                requesters_email="NOISE_EMAIL_3",
            ),
        ]
        pyramid_request.db.add_all(application_instances)
        return application_instances
