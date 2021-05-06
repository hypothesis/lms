from unittest import mock

import pytest

from lms.services import ConsumerKeyError
from lms.services.application_instance_getter import (
    application_instance_getter_service_factory,
)
from tests import factories


class TestApplicationInstanceGetter:
    def test_developer_key_returns_the_developer_key(
        self, ai_getter, test_application_instance
    ):
        assert ai_getter.developer_key() == test_application_instance.developer_key

    def test_developer_key_returns_None_if_ApplicationInstance_has_no_developer_key(
        self, ai_getter, test_application_instance
    ):
        test_application_instance.developer_key = None

        assert ai_getter.developer_key() is None

    @pytest.mark.usefixtures("unknown_consumer_key")
    def test_developer_key_raises_if_consumer_key_unknown(self, ai_getter):
        with pytest.raises(ConsumerKeyError):
            ai_getter.developer_key()

    def test_lms_url_returns_the_lms_url(self, ai_getter, test_application_instance):
        assert ai_getter.lms_url() == test_application_instance.lms_url

    @pytest.mark.usefixtures("unknown_consumer_key")
    def test_lms_url_raises_if_consumer_key_unknown(self, ai_getter):
        with pytest.raises(ConsumerKeyError):
            ai_getter.lms_url()

    @pytest.mark.parametrize(
        "developer_key,expected_result", [("test_developer_key", True), (None, False)]
    )
    def test_canvas_sections_supported(
        self, pyramid_request, test_application_instance, developer_key, expected_result
    ):
        ai_getter = application_instance_getter_service_factory(
            mock.sentinel.context, pyramid_request
        )
        test_application_instance.developer_key = developer_key

        assert ai_getter.canvas_sections_supported() == expected_result

    @pytest.mark.usefixtures("unknown_consumer_key")
    def test_canvas_sections_supported_returns_False_if_consumer_key_unknown(
        self, ai_getter
    ):
        assert not ai_getter.canvas_sections_supported()

    def test_settings(self, ai_getter, test_application_instance):
        assert ai_getter.settings() == test_application_instance.settings

    def test_shared_secret_returns_the_shared_secret(
        self, ai_getter, test_application_instance
    ):
        assert ai_getter.shared_secret() == test_application_instance.shared_secret

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
        return factories.ApplicationInstance(
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
        )

    @pytest.fixture(autouse=True)
    def application_instances(self):
        """Add some "noise" application instances."""
        # Add some "noise" application instances to the DB for every test, to
        # make the tests more realistic.
        return factories.ApplicationInstance.create_batch(size=3)

    @pytest.fixture
    def unknown_consumer_key(self, pyramid_request):
        pyramid_request.lti_user = pyramid_request.lti_user._replace(
            oauth_consumer_key="UNKNOWN_CONSUMER_KEY"
        )
        return pyramid_request
