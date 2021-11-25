from unittest.mock import sentinel

import pytest
from aiohttp import TooManyRedirects
from aioresponses import aioresponses

from lms.services import ExternalRequestError
from lms.services.async_oauth_http import AsyncOAuthHTTPService, factory


class TestAsyncOAuthHTTPService:
    def test_request_success(
        self, svc, urls, with_successful_responses, oauth2_token_service
    ):
        responses = svc.request("GET", urls)

        for url, response in zip(urls, responses):
            assert response.status == 200
            assert response.headers["url"] == url

        for request in with_successful_responses.requests.values():
            request_kwargs = request[0].kwargs

            assert request_kwargs["timeout"] == 10
            assert (
                request_kwargs["headers"]["Authorization"]
                == f"Bearer {oauth2_token_service.get().access_token}"
            )

    @pytest.mark.usefixtures("with_one_failed_response")
    def test_request_with_failure(self, svc, urls):
        with pytest.raises(ExternalRequestError):
            svc.request("GET", urls)

    @pytest.fixture
    def with_successful_responses(self, urls):
        with aioresponses() as m:
            for url in urls:
                m.get(url, headers=dict(url=url))

            yield m

    @pytest.fixture
    def with_one_failed_response(self, urls):
        with aioresponses() as m:
            for url in urls[:-1]:
                m.get(url, status=200)
            m.get(urls[-1], exception=TooManyRedirects("info", "history"))

            yield m

    @pytest.fixture
    def urls(self):
        """Return the URLs that we'll be sending test requests to."""
        return ["https://example.com/example", "https://example.com/another"]

    @pytest.fixture
    def svc(self, oauth2_token_service):
        return AsyncOAuthHTTPService(oauth2_token_service)


class TestFactory:
    @pytest.mark.usefixtures("oauth2_token_service")
    def test_it(self, pyramid_request):
        assert isinstance(
            factory(sentinel.context, pyramid_request), AsyncOAuthHTTPService
        )
