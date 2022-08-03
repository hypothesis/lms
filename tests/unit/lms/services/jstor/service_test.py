from datetime import timedelta
from functools import partial
from unittest.mock import sentinel

import pytest

from lms.services import ExternalRequestError
from lms.services.jstor.service import JSTORService
from tests import factories

API_URL = "http://api.jstor.org"


class TestJSTORService:
    @pytest.mark.parametrize("enabled", (True, False, None))
    @pytest.mark.parametrize("site_code", ("code", None, ""))
    def test_enabled(self, get_service, enabled, site_code):
        svc = get_service(enabled=enabled, site_code=site_code)

        assert svc.enabled == bool(enabled and site_code)

    @pytest.mark.parametrize(
        "url,expected",
        [
            ("jstor://ARTICLE_ID", f"{API_URL}/pdf/10.2307/ARTICLE_ID"),
            ("jstor://PREFIX/SUFFIX", f"{API_URL}/pdf/PREFIX/SUFFIX"),
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
            url=expected, headers={"Authorization": "Bearer TOKEN"}, params=None
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
        "article_id, expected_api_url",
        [
            # Typical JSTOR article, with no DOI prefix given
            ("12345", f"{API_URL}/metadata/10.2307/12345"),
            # Article ID that needs to be encoded
            ("123:45", f"{API_URL}/metadata/10.2307/123%3A45"),
            # Article with custom DOI prefix
            ("10.123/12345", f"{API_URL}/metadata/10.123/12345"),
        ],
    )
    def test_get_article_metadata(
        self, svc, http_service, article_id, expected_api_url, ArticleMetadata
    ):
        response = svc.get_article_metadata(article_id)

        http_service.get.assert_called_with(
            url=expected_api_url, headers={"Authorization": "Bearer TOKEN"}, params=None
        )
        ArticleMetadata.from_response.assert_called_once_with(
            http_service.get.return_value
        )
        meta = ArticleMetadata.from_response.return_value
        assert response == meta.as_dict.return_value

    @pytest.mark.parametrize(
        "article_id,expected_api_url",
        [
            # Typical JSTOR article, with no DOI prefix given
            ("12345", f"{API_URL}/thumbnail/10.2307/12345"),
            # Article ID that needs to be encoded
            ("123:45", f"{API_URL}/thumbnail/10.2307/123%3A45"),
            # Article with custom DOI prefix
            ("10.123/12345", f"{API_URL}/thumbnail/10.123/12345"),
        ],
    )
    def test_thumbnail(self, svc, http_service, article_id, expected_api_url):
        http_service.get.return_value = factories.requests.Response(
            raw="data:image/jpeg;base64,ABCD"
        )

        data_uri = svc.thumbnail(article_id)

        http_service.get.assert_called_with(
            url=expected_api_url,
            headers={"Authorization": "Bearer TOKEN"},
            params={"offset": 1, "width": 280},
        )
        assert data_uri == "data:image/jpeg;base64,ABCD"

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
    def get_service(self, http_service):
        return partial(
            JSTORService,
            api_url=API_URL,
            secret=sentinel.secret,
            enabled=True,
            site_code=sentinel.site_code,
            http_service=http_service,
        )

    @pytest.fixture
    def svc(self, get_service):
        return get_service()

    @pytest.fixture
    def ArticleMetadata(self, patch):
        return patch("lms.services.jstor.service.ArticleMetadata")

    @pytest.fixture
    def via_url(self, patch):
        return patch("lms.services.jstor.service.via_url")

    @pytest.fixture(autouse=True)
    def JWTService(self, patch):
        svc = patch("lms.services.jstor.service.JWTService")
        svc.encode_with_secret.return_value = "TOKEN"
        return svc
