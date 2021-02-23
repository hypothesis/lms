from unittest.mock import sentinel

import pytest
from h_matchers import Any
from oauthlib.oauth1 import SIGNATURE_HMAC_SHA1, SIGNATURE_TYPE_BODY

from lms.services.vitalsource import VitalSourceService, factory
from tests import factories


class TestVitalSourceService:
    def test_it_generates_lti_launch_form_params(self, svc, lti_user):
        launch_url, params = svc.get_launch_params("book-id", "/abc", lti_user)

        # Ignore OAuth signature params in this test.
        params = {k: v for (k, v) in params.items() if not k.startswith("oauth_")}

        assert launch_url == "https://bc.vitalsource.com/books/book-id"
        assert params == {
            "user_id": "teststudent",
            "roles": "Learner",
            "context_id": "testcourse",
            "launch_presentation_document_target": "window",
            "lti_version": "LTI-1p0",
            "lti_message_type": "basic-lti-launch-request",
            "custom_book_location": "/cfi/abc",
        }

    def test_it_uses_correct_launch_key_and_secret_to_sign_params(
        self, svc, lti_user, OAuth1Client
    ):
        svc.get_launch_params("book-id", "/cfi", lti_user)

        OAuth1Client.assert_called_with(
            "lti_launch_key",
            "lti_launch_secret",
            signature_method=SIGNATURE_HMAC_SHA1,
            signature_type=SIGNATURE_TYPE_BODY,
        )

    def test_it_signs_lti_launch_form_params(self, svc, lti_user):
        _, params = svc.get_launch_params("book-id", "/cfi", lti_user)

        # Ignore non-OAuth signature params in this test.
        params = {k: v for (k, v) in params.items() if k.startswith("oauth_")}

        assert params == {
            "oauth_consumer_key": "lti_launch_key",
            "oauth_nonce": Any.string.matching("[0-9]+"),
            "oauth_signature": Any.string.matching("[0-9a-zA-Z+=]+"),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": Any.string.matching("[0-9]+"),
            "oauth_version": "1.0",
        }

    @pytest.fixture
    def svc(self):
        return VitalSourceService("lti_launch_key", "lti_launch_secret")

    @pytest.fixture
    def lti_user(self):
        return factories.LTIUser(user_id="teststudent", roles="Learner")

    @pytest.fixture
    def OAuth1Client(self, patch):
        return patch("lms.services.vitalsource.oauthlib.oauth1.Client")


class TestFactory:
    def test_it(self, pyramid_request, VitalSourceService):
        svc = factory(sentinel.context, pyramid_request)

        VitalSourceService.assert_called_once_with(
            sentinel.vs_lti_launch_key, sentinel.vs_lti_launch_secret
        )
        assert svc == VitalSourceService.return_value

    @pytest.mark.parametrize(
        "name_of_missing_envvar",
        ["vitalsource_lti_launch_key", "vitalsource_lti_launch_secret"],
    )
    def test_it_raises_if_an_envvar_is_missing(
        self, pyramid_request, name_of_missing_envvar
    ):
        del pyramid_request.registry.settings[name_of_missing_envvar]

        with pytest.raises(KeyError):
            factory(sentinel.context, pyramid_request)

    @pytest.fixture
    def pyramid_config(self, pyramid_config):
        pyramid_config.registry.settings[
            "vitalsource_lti_launch_key"
        ] = sentinel.vs_lti_launch_key
        pyramid_config.registry.settings[
            "vitalsource_lti_launch_secret"
        ] = sentinel.vs_lti_launch_secret
        return pyramid_config

    @pytest.fixture(autouse=True)
    def VitalSourceService(self, patch):
        return patch("lms.services.vitalsource.VitalSourceService")
