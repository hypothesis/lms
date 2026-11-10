from unittest.mock import Mock, sentinel

import pytest
from aiohttp import ClientResponse, TooManyRedirects
from aioresponses import aioresponses

from lms.services.async_oauth_http import AsyncOAuthHTTPService, factory
from lms.services.exceptions import ExternalAsyncRequestError


class _ClientResponse(ClientResponse):
    """ClientResponse that works with aioresponses and aiohttp>=3.14.4.

    aiohttp 3.14.4 added a required `stream_writer` argument to
    ClientResponse.__init__() but aioresponses (<= 0.7.9, the latest release)
    doesn't pass it when building mocked responses.

    Upstream: https://github.com/pnuckowski/aioresponses/issues/289 and the
    fix in https://github.com/pnuckowski/aioresponses/pull/288 (still open).
    Once a release includes it, this class and the `response_class=`
    arguments below can go.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("stream_writer", Mock(output_size=0))
        super().__init__(*args, **kwargs)


@pytest.mark.filterwarnings(
    "ignore:Setting custom ClientSession._resolve_charset attribute is discouraged"
)
class TestAsyncOAuthHTTPService:
    def test_request_success(
        self, svc, urls, with_successful_responses, oauth2_token_service
    ):
        responses = svc.request("GET", urls)

        for url, response in zip(urls, responses, strict=False):
            assert response.status == 200
            assert response.headers["url"] == url
            assert response.sync_text == '["ASYNC RESPONSE"]'
            assert response.json() == ["ASYNC RESPONSE"]

        for request in with_successful_responses.requests.values():
            request_kwargs = request[0].kwargs

            assert request_kwargs["timeout"] == 10
            assert (
                request_kwargs["headers"]["Authorization"]
                == f"Bearer {oauth2_token_service.get().access_token}"
            )

    @pytest.mark.usefixtures("with_one_failed_response")
    def test_request_with_failure(self, svc, urls):
        with pytest.raises(ExternalAsyncRequestError):
            svc.request("GET", urls)

    @pytest.fixture
    def with_successful_responses(self, urls):
        with aioresponses() as m:
            for url in urls:
                m.get(
                    url,
                    headers={"url": url},
                    body='["ASYNC RESPONSE"]',
                    response_class=_ClientResponse,
                )

            yield m

    @pytest.fixture
    def with_one_failed_response(self, urls):
        with aioresponses() as m:
            for url in urls[:-1]:
                m.get(url, status=200, response_class=_ClientResponse)
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
