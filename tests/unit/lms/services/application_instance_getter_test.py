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
        assert ai_getter.developer_key() == "TEST_DEVELOPER_KEY"

    def test_developer_key_returns_None_if_ApplicationInstance_has_no_developer_key(
        self, ai_getter, test_application_instance
    ):
        test_application_instance.developer_key = None

        assert ai_getter.developer_key() is None

    @pytest.mark.usefixtures("unknown_consumer_key")
    def test_developer_key_raises_if_consumer_key_unknown(self, ai_getter):
        with pytest.raises(ConsumerKeyError):
            ai_getter.developer_key()

    def test_developer_secret_returns_the_decrypted_developer_secret(
        self, ai_getter, pyramid_request, test_application_instance
    ):
        test_application_instance.aes_cipher_iv = _build_aes_iv()
        test_application_instance.developer_secret = _encrypt_oauth_secret(
            b"TEST_DEVELOPER_SECRET",
            pyramid_request.registry.settings["aes_secret"],
            test_application_instance.aes_cipher_iv,
        )

        assert ai_getter.developer_secret() == b"TEST_DEVELOPER_SECRET"

    def test_developer_secret_returns_None_if_ApplicationInstance_has_no_developer_secret(
        self, ai_getter
    ):
        assert ai_getter.developer_secret() is None

    @pytest.mark.usefixtures("unknown_consumer_key")
    def test_developer_secret_raises_if_consumer_key_unknown(self, ai_getter):
        with pytest.raises(ConsumerKeyError):
            ai_getter.developer_secret()

    def test_lms_url_returns_the_lms_url(self, ai_getter):
        assert ai_getter.lms_url() == "TEST_LMS_URL"

    @pytest.mark.usefixtures("unknown_consumer_key")
    def test_lms_url_raises_if_consumer_key_unknown(self, ai_getter):
        with pytest.raises(ConsumerKeyError):
            ai_getter.lms_url()

    @pytest.mark.parametrize("flag", [True, False])
    def test_provisioning_returns_the_provisioning_flag(
        self, ai_getter, flag, test_application_instance
    ):
        test_application_instance.provisioning = flag

        assert ai_getter.provisioning_enabled() == flag

    @pytest.mark.usefixtures("unknown_consumer_key")
    def test_provisioning_returns_False_if_consumer_key_unknown(self, ai_getter):
        assert not ai_getter.provisioning_enabled()

    @pytest.mark.parametrize(
        "params",
        [
            dict(
                feature_flag=True,
                developer_key="test_developer_key",
                canvas_sections_enabled=True,
                expected_result=True,
            ),
            dict(
                feature_flag=False,
                developer_key="test_developer_key",
                canvas_sections_enabled=True,
                expected_result=False,
            ),
            dict(
                feature_flag=True,
                developer_key=None,
                canvas_sections_enabled=True,
                expected_result=False,
            ),
            dict(
                feature_flag=True,
                developer_key="test_developer_key",
                canvas_sections_enabled=False,
                expected_result=False,
            ),
            dict(
                feature_flag=False,
                developer_key=None,
                canvas_sections_enabled=False,
                expected_result=False,
            ),
        ],
    )
    def test_canvas_sections_enabled(
        self, pyramid_request, test_application_instance, params,
    ):
        if params["feature_flag"]:
            enable_section_groups_feature_flag(pyramid_request)

        ai_getter = application_instance_getter_service_factory(
            mock.sentinel.context, pyramid_request
        )
        test_application_instance.developer_key = params["developer_key"]
        # pylint: disable=protected-access
        test_application_instance._settings = {
            "canvas": {"sections_enabled": params["canvas_sections_enabled"]}
        }

        assert ai_getter.canvas_sections_enabled() == params["expected_result"]

    @pytest.mark.usefixtures(
        "unknown_consumer_key", "section_groups_feature_flag_enabled"
    )
    def test_canvas_sections_enabled_returns_False_if_consumer_key_unknown(
        self, ai_getter
    ):
        assert not ai_getter.canvas_sections_enabled()

    def test_shared_secret_returns_the_shared_secret(self, ai_getter):
        assert ai_getter.shared_secret() == "TEST_SHARED_SECRET"

    @pytest.mark.usefixtures("unknown_consumer_key")
    def test_shared_secret_raises_if_consumer_key_unknown(self, ai_getter):
        with pytest.raises(ConsumerKeyError):
            ai_getter.shared_secret()

    @pytest.fixture
    def ai_getter(self, pyramid_request):
        return application_instance_getter_service_factory(
            mock.sentinel.context, pyramid_request
        )

    @pytest.fixture(autouse=True)
    def test_application_instance(self, pyramid_request):
        application_instance = ApplicationInstance(
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
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

    @pytest.fixture
    def unknown_consumer_key(self, pyramid_request):
        pyramid_request.lti_user = pyramid_request.lti_user._replace(
            oauth_consumer_key="UNKNOWN_CONSUMER_KEY"
        )
        return pyramid_request


def enable_section_groups_feature_flag(pyramid_request):
    """
    Enable the "section_groups" feature flag.

    Also disables all other feature flags.
    """
    pyramid_request.feature.side_effect = lambda flag: flag == "section_groups"


@pytest.fixture
def section_groups_feature_flag_enabled(pyramid_request):
    enable_section_groups_feature_flag(pyramid_request)
