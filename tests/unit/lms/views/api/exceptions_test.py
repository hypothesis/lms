import pytest
from pyramid.httpexceptions import HTTPBadRequest

from lms.services import CanvasAPIError, CanvasAPIPermissionError
from lms.validation import ValidationError
from lms.views.api.exceptions import APIExceptionViews


class TestSchemaValidationError:
    def test_it(self, pyramid_request, views):
        json_data = views.validation_error()

        assert pyramid_request.response.status_code == 422
        assert json_data == {
            "message": "Unable to process the contained instructions",
            "details": "foobar",
        }

    @pytest.fixture
    def context(self):
        return ValidationError(messages="foobar")


class TestOAuth2TokenError:
    def test_it(self, pyramid_request, views):
        json_data = views.oauth2_token_error()

        assert pyramid_request.response.status_code == 400
        assert json_data == {}


class TestExternalRequestError:
    def test_it(self, pyramid_request, views, report_exception):
        json_data = views.external_request_error()

        report_exception.assert_called_once_with()
        assert pyramid_request.response.status_code == 400
        assert json_data == {
            "message": "test_explanation",
            "details": {"foo": "bar"},
        }

    @pytest.fixture
    def context(self):
        return CanvasAPIError(explanation="test_explanation", details={"foo": "bar"})


class TestNotFound:
    def test_it_sets_response_status(self, pyramid_request, views):
        views.notfound()

        assert pyramid_request.response.status_int == 404

    def test_it_shows_a_generic_error_message_to_the_user(self, views):
        result = views.notfound()

        assert result["message"] == "Endpoint not found."


class TestForbidden:
    def test_it_sets_response_status(self, pyramid_request, views):
        views.forbidden()

        assert pyramid_request.response.status_int == 403

    def test_it_shows_a_generic_error_message_to_the_user(self, views):
        result = views.forbidden()

        assert result["message"] == "You're not authorized to view this page."


class TestHTTPBadRequest:
    def test_it(self, pyramid_request, views):
        json_data = views.http_bad_request()

        assert pyramid_request.response.status_int == 400
        assert json_data == {"message": "test_explanation"}

    @pytest.fixture
    def context(self):
        return HTTPBadRequest("test_explanation")


class TestAPIError:
    def test_it_with_a_CanvasAPIPermissionError(self, pyramid_request, views):
        context = views.context = CanvasAPIPermissionError(details={"foo": "bar"})

        json_data = views.api_error()

        assert pyramid_request.response.status_code == 400
        assert json_data == {
            "error_code": context.error_code,
            "details": context.details,
        }

    def test_it_with_an_unexpected_error(self, pyramid_request, views):
        views.context = RuntimeError("Totally unexpected")

        json_data = views.api_error()

        assert pyramid_request.response.status_code == 500
        assert json_data == {
            "message": (
                "A problem occurred while handling this request. Hypothesis has been"
                " notified."
            )
        }


@pytest.fixture
def context():
    return None


@pytest.fixture
def views(context, pyramid_request):
    return APIExceptionViews(context, pyramid_request)


@pytest.fixture(autouse=True)
def report_exception(patch):
    return patch("lms.views.api.exceptions.report_exception")
