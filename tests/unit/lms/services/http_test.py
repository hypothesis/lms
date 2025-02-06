from unittest.mock import create_autospec, sentinel

import pytest
import requests
from requests import RequestException

from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService, factory


class TestHTTPService:
    def test_request(self, svc, passed_args):
        response = svc.request(sentinel.method, sentinel.url, **passed_args)

        svc.session.request.assert_called_once_with(
            sentinel.method, sentinel.url, **passed_args
        )
        assert response == svc.session.request.return_value

    @pytest.mark.parametrize("method", ["get", "put", "post", "patch", "delete"])
    def test_convenience_methods(self, svc, method, passed_args):
        response = getattr(svc, method.lower())(sentinel.url, **passed_args)

        svc.session.request.assert_called_once_with(
            method.upper(), sentinel.url, **passed_args
        )
        assert response == svc.session.request.return_value

    def test_request_defaults(self, svc):
        svc.request(sentinel.method, sentinel.url)

        svc.session.request.assert_called_once_with(
            sentinel.method, sentinel.url, timeout=(10, 10)
        )

    def test_it_raises_if_sending_the_request_fails(self, svc):
        svc.session.request.side_effect = RequestException(
            request=sentinel.err_request, response=sentinel.err_response
        )

        with pytest.raises(ExternalRequestError) as exc_info:
            svc.request("GET", "https://example.com")

        assert exc_info.value.request == sentinel.err_request
        assert exc_info.value.response is None

    def test_it_raises_if_the_response_is_an_error(self, svc):
        response = svc.session.request.return_value
        response.raise_for_status.side_effect = RequestException(
            request=sentinel.err_request, response=sentinel.err_response
        )

        with pytest.raises(ExternalRequestError) as exc_info:
            svc.request("GET", "https://example.com")

        assert exc_info.value.request == sentinel.err_request
        assert exc_info.value.response == response

    @pytest.fixture
    def passed_args(self):
        return {
            "headers": sentinel.headers,
            "params": sentinel.params,
            "json": sentinel.json,
            "data": sentinel.data,
            "auth": sentinel.auth,
            "timeout": sentinel.timeout,
        }

    @pytest.fixture
    def svc(self):
        svc = HTTPService()
        svc.session = create_autospec(requests.Session, instance=True, spec_set=True)
        return svc


class TestFactory:
    def test_it(self, pyramid_request, HTTPService):
        svc = factory(sentinel.context, pyramid_request)

        HTTPService.assert_called_once_with()
        assert svc == HTTPService.return_value

    @pytest.fixture
    def HTTPService(self, patch):
        return patch("lms.services.http.HTTPService")
