import pytest
from h_matchers import Any
from oauthlib.oauth1 import SIGNATURE_HMAC_SHA1, SIGNATURE_TYPE_BODY

from lms.services.vitalsource import VitalSourceService
from tests import factories


class TestVitalSourceService:
    def test_it_generates_lti_launch_form_params(self, pyramid_request, lti_user):
        svc = VitalSourceService({}, pyramid_request)

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
        self, pyramid_request, lti_user, OAuth1Client
    ):
        svc = VitalSourceService({}, pyramid_request)

        svc.get_launch_params("book-id", "/cfi", lti_user)

        OAuth1Client.assert_called_with(
            pyramid_request.registry.settings["vitalsource_launch_key"],
            pyramid_request.registry.settings["vitalsource_launch_secret"],
            signature_method=SIGNATURE_HMAC_SHA1,
            signature_type=SIGNATURE_TYPE_BODY,
        )

    def test_it_signs_lti_launch_form_params(self, pyramid_request, lti_user):
        svc = VitalSourceService({}, pyramid_request)

        _, params = svc.get_launch_params("book-id", "/cfi", lti_user)

        # Ignore non-OAuth signature params in this test.
        params = {k: v for (k, v) in params.items() if k.startswith("oauth_")}

        assert params == {
            "oauth_consumer_key": "test_vs_launch_key",
            "oauth_nonce": Any.string.matching("[0-9]+"),
            "oauth_signature": Any.string.matching("[0-9a-zA-Z+=]+"),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": Any.string.matching("[0-9]+"),
            "oauth_version": "1.0",
        }

    def test_it_raises_if_launch_key_not_set(self, pyramid_request):
        del pyramid_request.registry.settings["vitalsource_launch_key"]

        with pytest.raises(KeyError):
            VitalSourceService({}, pyramid_request)

    def test_it_raises_if_launch_secret_not_set(self, pyramid_request):
        del pyramid_request.registry.settings["vitalsource_launch_secret"]

        with pytest.raises(KeyError):
            VitalSourceService({}, pyramid_request)

    @pytest.fixture
    def lti_user(self):
        return factories.LTIUser(user_id="teststudent", roles="Learner")

    @pytest.fixture
    def OAuth1Client(self, patch):
        return patch("lms.services.vitalsource.oauthlib.oauth1.Client")
