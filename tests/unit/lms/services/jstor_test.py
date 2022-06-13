from datetime import timedelta
from functools import partial
from unittest.mock import sentinel

import pytest

from lms.models import ApplicationSettings
from lms.services import ExternalRequestError
from lms.services.jstor import JSTORService, factory
from tests import factories

JSTOR_API_URL = "http://api.jstor.org"


class TestJSTORService:
    @pytest.mark.parametrize("enabled", (True, False, None))
    @pytest.mark.parametrize("site_code", ("code", None, ""))
    def test_enabled(self, get_service, enabled, site_code):
        svc = get_service(enabled=enabled, site_code=site_code)

        assert svc.enabled == bool(enabled and site_code)

    @pytest.mark.parametrize(
        "url,expected",
        [
            (
                "jstor://ARTICLE_ID",
                f"{JSTOR_API_URL}/pdf-url/10.2307/ARTICLE_ID",
            ),
            ("jstor://PREFIX/SUFFIX", f"{JSTOR_API_URL}/pdf-url/PREFIX/SUFFIX"),
        ],
    )
    def test_via_url(
        self, svc, pyramid_request, JWTService, http_service, via_url, url, expected
    ):
        url = svc.via_url(pyramid_request, document_url=url)

        JWTService.encode_with_secret.assert_called_once_with(
            {"site_code": sentinel.site_code},
            sentinel.secret,
            lifetime=timedelta(hours=1),
        )

        http_service.get.assert_called_once_with(
            url=expected,
            headers={"Authorization": "Bearer TOKEN"},
        )

        via_url.assert_called_once_with(
            pyramid_request,
            http_service.get.return_value.text,
            content_type="pdf",
            options={"via.client.contentPartner": "jstor"},
        )

        assert url == via_url.return_value

    def test_via_url_with_bad_return_value_from_s3(
        self, svc, http_service, pyramid_request
    ):
        http_service.get.return_value = factories.requests.Response(raw="NOT A URL")

        with pytest.raises(ExternalRequestError):
            svc.via_url(pyramid_request, document_url="jstor://ANY")

    @pytest.mark.parametrize(
        "article_id, api_response, expected_api_url, expected_metadata",
        [
            # Typical JSTOR article, with no DOI prefix given
            (
                "12345",
                {"title": ["test title"]},
                f"{JSTOR_API_URL}/metadata/10.2307/12345",
                {"title": "test title"},
            ),
            # Article ID that needs to be encoded
            (
                "123:45",
                {"title": ["test title"]},
                f"{JSTOR_API_URL}/metadata/10.2307/123%3A45",
                {"title": "test title"},
            ),
            # Article with custom DOI prefix
            (
                "10.123/12345",
                {"title": ["test title"]},
                f"{JSTOR_API_URL}/metadata/10.123/12345",
                {"title": "test title"},
            ),
            # No title
            (
                "12345",
                {"title": []},
                f"{JSTOR_API_URL}/metadata/10.2307/12345",
                {"title": None},
            ),
        ],
    )
    def test_metadata(
        self,
        svc,
        http_service,
        api_response,
        article_id,
        expected_api_url,
        expected_metadata,
    ):
        http_service.get.return_value = factories.requests.Response(
            json_data=api_response
        )

        metadata = svc.metadata(article_id)

        http_service.get.assert_called_with(
            url=expected_api_url, headers={"Authorization": "Bearer TOKEN"}
        )
        assert metadata == expected_metadata

    def test_metadata_raises_if_schema_mismatch(self, svc, http_service):
        invalid_api_response = {"title": "This should be a list"}
        http_service.get.return_value = factories.requests.Response(
            json_data=invalid_api_response
        )

        with pytest.raises(ExternalRequestError) as exc:
            svc.metadata("1234")

        assert exc.value.validation_errors is not None

    @pytest.mark.parametrize(
        "article_id, api_response, expected_api_url",
        [
            # Typical JSTOR article, with no DOI prefix given
            (
                "12345",
                "data:image/jpeg;base64,ABCD",
                f"{JSTOR_API_URL}/thumbnail/10.2307/12345",
            ),
            # Article ID that needs to be encoded
            (
                "123:45",
                "data:image/jpeg;base64,ABCD",
                f"{JSTOR_API_URL}/thumbnail/10.2307/123%3A45",
            ),
            # Article with custom DOI prefix
            (
                "10.123/12345",
                "data:image/jpeg;base64,ABCD",
                f"{JSTOR_API_URL}/thumbnail/10.123/12345",
            ),
        ],
    )
    def test_thumbnail(
        self, svc, http_service, article_id, api_response, expected_api_url
    ):
        http_service.get.return_value = factories.requests.Response(raw=api_response)

        data_uri = svc.thumbnail(article_id)

        http_service.get.assert_called_with(
            url=expected_api_url, headers={"Authorization": "Bearer TOKEN"}
        )
        assert data_uri == api_response

    def test_thumbnail_raises_if_response_not_image(self, svc, http_service):
        http_service.get.return_value = factories.requests.Response(
            raw="not-a-data-uri"
        )

        with pytest.raises(ExternalRequestError) as exc_info:
            svc.thumbnail("1234")

        assert exc_info.value.message.startswith("Expected to get data URI")

    @pytest.fixture
    def http_service(self, http_service):
        http_service.get.return_value = factories.requests.Response(
            raw="https://s3.example.com/pdf"
        )

        return http_service

    @pytest.fixture
    def via_url(self, patch):
        return patch("lms.services.jstor.via_url")

    @pytest.fixture
    def get_service(self, http_service):
        return partial(
            JSTORService,
            api_url=JSTOR_API_URL,
            secret=sentinel.secret,
            enabled=True,
            site_code=sentinel.site_code,
            http_service=http_service,
        )

    @pytest.fixture
    def svc(self, get_service):
        return get_service()

    @pytest.fixture(autouse=True)
    def JWTService(self, patch):
        svc = patch("lms.services.jstor.JWTService")
        svc.encode_with_secret.return_value = "TOKEN"
        return svc


class TestFactory:
    def test_it(
        self, pyramid_request, application_instance_service, http_service, JSTORService
    ):
        application_instance_service.get_current.return_value.settings = (
            ApplicationSettings(
                {
                    "jstor": {
                        "enabled": sentinel.jstor_enabled,
                        "site_code": sentinel.jstor_site_code,
                    }
                }
            )
        )
        pyramid_request.registry.settings.update(
            {
                "jstor_api_url": sentinel.jstor_api_url,
                "jstor_api_secret": sentinel.jstor_api_secret,
            }
        )

        svc = factory(sentinel.context, pyramid_request)

        JSTORService.assert_called_once_with(
            api_url=sentinel.jstor_api_url,
            secret=sentinel.jstor_api_secret,
            enabled=sentinel.jstor_enabled,
            site_code=sentinel.jstor_site_code,
            http_service=http_service,
        )
        assert svc == JSTORService.return_value

    @pytest.fixture(autouse=True)
    def JSTORService(self, patch):
        return patch("lms.services.jstor.JSTORService")
