from unittest import mock
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from oauthlib.oauth1 import SIGNATURE_HMAC_SHA1, SIGNATURE_TYPE_BODY

from lms.services.exceptions import HTTPError
from lms.services.vitalsource import VitalSourceService, factory
from tests import factories


class TestVitalSourceService:
    @pytest.mark.parametrize(
        "lti_key,lti_secret,api_key",
        [
            (None, "launch-secret", "api-key"),
            ("launch-key", "launch-secret", None),
            ("launch-key", None, "api-key"),
            ("", "", ""),
        ],
    )
    def test_init_raises_if_launch_credentials_invalid(
        self, http_service, lti_key, lti_secret, api_key
    ):
        with pytest.raises(ValueError, match="VitalSource credentials are missing"):
            VitalSourceService(http_service, lti_key, lti_secret, api_key)

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

        base64_char = "[0-9a-zA-Z+=/]"
        assert params == {
            "oauth_consumer_key": "lti_launch_key",
            "oauth_nonce": Any.string.matching("[0-9]+"),
            "oauth_signature": Any.string.matching(f"{base64_char}+"),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": Any.string.matching("[0-9]+"),
            "oauth_version": "1.0",
        }

    def test_api_get(self, svc, http_service):
        svc._api_get("endpoint/path")  # pylint: disable=protected-access

        http_service.get.assert_called_once_with(
            "https://api.vitalsource.com/v4/endpoint/path",
            headers={"X-VitalSource-API-Key": "api_key"},
        )

    def test_book_info_api(self, svc, book_info_schema):
        with mock.patch.object(VitalSourceService, "_api_get") as api_get:
            book_toc = svc.book_info("BOOK_ID")
            api_get.assert_called_once_with("products/BOOK_ID")

        assert book_toc == book_info_schema.parse.return_value

    def test_book_info_not_found(self, svc):
        with mock.patch.object(
            VitalSourceService,
            "_api_get",
            side_effect=HTTPError(factories.requests.Response(status_code=404)),
        ):
            assert svc.book_info("BOOK_ID") is None

    def test_book_info_error(self, svc):
        with mock.patch.object(
            VitalSourceService,
            "_api_get",
            side_effect=HTTPError(factories.requests.Response(status_code=500)),
        ):
            with pytest.raises(HTTPError):
                svc.book_info("BOOK_ID")

    def test_book_toc_api(self, svc, book_toc_schema):
        with mock.patch.object(VitalSourceService, "_api_get") as api_get:
            book_toc = svc.book_toc("BOOK_ID")
            api_get.assert_called_once_with("products/BOOK_ID/toc")

        assert book_toc == book_toc_schema.parse.return_value

    def test_book_toc_not_found(self, svc):
        with mock.patch.object(
            VitalSourceService,
            "_api_get",
            side_effect=HTTPError(factories.requests.Response(status_code=404)),
        ):
            assert svc.book_toc("BOOK_ID") is None

    def test_book_toc_error(self, svc):
        with mock.patch.object(
            VitalSourceService,
            "_api_get",
            side_effect=HTTPError(factories.requests.Response(status_code=500)),
        ):
            with pytest.raises(HTTPError):
                svc.book_toc("BOOK_ID")

    @pytest.fixture
    def svc(self, http_service):
        return VitalSourceService(
            http_service, "lti_launch_key", "lti_launch_secret", "api_key"
        )

    @pytest.fixture
    def lti_user(self):
        return factories.LTIUser(user_id="teststudent", roles="Learner")

    @pytest.fixture
    def OAuth1Client(self, patch):
        return patch("lms.services.vitalsource.client.oauthlib.oauth1.Client")

    @pytest.fixture(autouse=True)
    def BookTOCSchema(self, patch):
        return patch("lms.services.vitalsource.client.BookTOCSchema")

    @pytest.fixture
    def book_toc_schema(self, BookTOCSchema):
        return BookTOCSchema.return_value

    @pytest.fixture(autouse=True)
    def BookInfoSchema(self, patch):
        return patch("lms.services.vitalsource.client.BookInfoSchema")

    @pytest.fixture
    def book_info_schema(self, BookInfoSchema):
        return BookInfoSchema.return_value


class TestFactory:
    def test_it(self, http_service, pyramid_request, VitalSourceService):
        svc = factory(sentinel.context, pyramid_request)

        VitalSourceService.assert_called_once_with(
            http_service,
            sentinel.vs_lti_launch_key,
            sentinel.vs_lti_launch_secret,
            sentinel.vs_api_key,
        )
        assert svc == VitalSourceService.return_value

    @pytest.mark.usefixtures("http_service")
    @pytest.mark.parametrize(
        "name_of_missing_envvar",
        [
            "vitalsource_lti_launch_key",
            "vitalsource_lti_launch_secret",
            "vitalsource_api_key",
        ],
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
        pyramid_config.registry.settings["vitalsource_api_key"] = sentinel.vs_api_key

        return pyramid_config

    @pytest.fixture(autouse=True)
    def VitalSourceService(self, patch):
        return patch("lms.services.vitalsource.client.VitalSourceService")
