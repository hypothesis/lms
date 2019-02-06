from unittest import mock

import pytest

from requests import ConnectionError
from requests import HTTPError
from requests import ReadTimeout
from requests import Response
from requests import TooManyRedirects

from lms.config.resources import LTILaunch
from lms.services.hapi import HypothesisAPIService
from lms.services import HAPIError
from lms.services import HAPINotFoundError


class TestAPIRequest:
    @pytest.mark.parametrize(
        "setting", ["h_client_id", "h_client_secret", "h_authority", "h_api_url"]
    )
    def test_it_crashes_if_a_required_setting_is_missing(
        self, pyramid_request, setting
    ):
        del pyramid_request.registry.settings[setting]

        with pytest.raises(KeyError, match=setting):
            HypothesisAPIService(None, pyramid_request)

    @pytest.mark.parametrize("verb", ["DELETE", "GET", "PATCH", "POST", "PUT"])
    def test_it_sends_requests_to_the_h_api(self, pyramid_request, requests, svc, verb):
        # Retrieve the method to call, e.g. HypothesisAPIService.delete() or .get().
        method = getattr(svc, verb.lower())

        method("path")

        requests.request.assert_called_once_with(
            method=verb,
            url="https://example.com/api/path",
            auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
            timeout=10,
        )

    def test_it_strips_leading_slashes_from_the_path(
        self, pyramid_request, requests, svc
    ):
        svc.request("POST", "/path")

        assert requests.request.call_args[1]["url"] == "https://example.com/api/path"

    # Instead of calling get() or post() etc you can also call request()
    # directly and pass in the HTTP verb as a string.
    def test_you_can_also_call_request_directly(self, pyramid_request, requests, svc):
        svc.request("PUT", "path")

        requests.request.assert_called_once_with(
            method="PUT",
            url="https://example.com/api/path",
            auth=("TEST_CLIENT_ID", "TEST_CLIENT_SECRET"),
            timeout=10,
        )

    def test_it_sends_data_as_json(self, pyramid_request, requests, svc):
        svc.post("path", data={"foo": "bar"})

        assert requests.request.call_args[1]["data"] == '{"foo": "bar"}'

    def test_it_sends_userid_as_x_forwarded_user(self, pyramid_request, requests, svc):
        svc.post("path", userid="acct:seanh@TEST_AUTHORITY")

        assert requests.request.call_args[1]["headers"]["X-Forwarded-User"] == (
            "acct:seanh@TEST_AUTHORITY"
        )

    @pytest.mark.parametrize(
        "exception", [ConnectionError(), HTTPError(), ReadTimeout(), TooManyRedirects()]
    )
    def test_it_raises_HAPIError_if_the_request_fails(
        self, exception, pyramid_request, requests, svc
    ):
        requests.request.side_effect = exception

        with pytest.raises(HAPIError) as exc_info:
            svc.post("path")

        # It records the requests exception that caused the HAPIError.
        assert exc_info.value.__cause__ == exception

    def test_it_raises_HAPINotFoundError_if_it_receives_a_404_response(
        self, pyramid_request, requests, svc
    ):
        requests.request.return_value.status_code = 404
        exception = HTTPError(response=requests.request.return_value)
        requests.request.return_value.raise_for_status.side_effect = exception

        with pytest.raises(HAPINotFoundError) as exc_info:
            svc.post("path")

        # It records the requests exception that caused the HAPIError.
        assert exc_info.value.__cause__ == exception

        assert (
            exc_info.value.response == requests.request.return_value
        ), "It passes the h API response to HAPIError so that it gets logged"

    def test_it_raises_HAPIError_if_it_receives_an_error_response(
        self, pyramid_request, requests, svc
    ):
        exception = HTTPError(response=requests.request.return_value)
        requests.request.return_value.raise_for_status.side_effect = exception

        with pytest.raises(HAPIError) as exc_info:
            svc.post("path")

        # It records the requests exception that caused the HAPIError.
        assert exc_info.value.__cause__ == exception

        assert (
            exc_info.value.response == requests.request.return_value
        ), "It passes the h API response to HAPIError so that it gets logged"

    def test_you_can_tell_it_not_to_raise_for_certain_error_statuses(
        self, pyramid_request, requests, svc
    ):
        response = Response()
        response.status_code = requests.request.return_value.status_code = 409
        requests.request.return_value.raise_for_status.side_effect = HTTPError(
            response=response
        )

        svc.post("path", statuses=[409])

    @pytest.fixture
    def context(self):
        context = mock.create_autospec(
            LTILaunch,
            spec_set=True,
            instance=True,
            h_userid="acct:seanh@TEST_AUTHORITY",
        )
        return context

    @pytest.fixture(autouse=True)
    def requests(self, patch):
        return patch("lms.services.hapi.requests")

    @pytest.fixture
    def svc(self, context, pyramid_request):
        return HypothesisAPIService(context, pyramid_request)
