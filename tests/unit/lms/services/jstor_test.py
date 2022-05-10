from functools import partial
from unittest.mock import MagicMock, sentinel

import pytest
from freezegun import freeze_time

from lms.models import ApplicationSettings
from lms.services import ExternalRequestError
from lms.services.jstor import JSTORService, factory


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
                "http://jstor.example.com/pdf-url/10.2307/ARTICLE_ID",
            ),
            ("jstor://PREFIX/SUFFIX", "http://jstor.example.com/pdf-url/PREFIX/SUFFIX"),
        ],
    )
    @freeze_time("2022-01-14")
    def test_via_url(
        self, svc, pyramid_request, jwt, http_service, via_url, url, expected
    ):
        jwt.encode.return_value = "TOKEN"

        url = svc.via_url(pyramid_request, document_url=url)

        jwt.encode.assert_called_once_with(
            {"exp": 1642122000, "site_code": sentinel.site_code},
            sentinel.secret,
            algorithm="HS256",
        )

        http_service.request.assert_called_once_with(
            method="GET",
            url=expected,
            headers={"Authorization": "Bearer TOKEN"},
        )

        via_url.assert_called_once_with(
            pyramid_request, http_service.request.return_value.text, content_type="pdf"
        )

        assert url == via_url.return_value

    def test_via_url_with_bad_return_value_from_s3(
        self, svc, http_service, pyramid_request
    ):
        http_service.request.return_value.text = "NOT A URL"

        with pytest.raises(ExternalRequestError):
            svc.via_url(pyramid_request, document_url="jstor://ANY")

    @pytest.fixture
    def http_service(self, http_service):
        http_service.request.return_value = MagicMock(text="https://s3.example.com/pdf")

        return http_service

    @pytest.fixture
    def via_url(self, patch):
        return patch("lms.services.jstor.via_url")

    @pytest.fixture
    def get_service(self, http_service):
        return partial(
            JSTORService,
            api_url="http://jstor.example.com",
            secret=sentinel.secret,
            enabled=True,
            site_code=sentinel.site_code,
            http_service=http_service,
        )

    @pytest.fixture
    def svc(self, get_service):
        return get_service()

    @pytest.fixture(autouse=True)
    def jwt(self, patch):
        return patch("lms.services.jstor.jwt")


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
