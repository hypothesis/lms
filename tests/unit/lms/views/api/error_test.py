from lms.services import CanvasAPIError, LTIOutcomesAPIError
from lms.validation import ValidationError
from lms.views.api import error


class TestSchemaValidationError:
    def test_it(self, pyramid_request):
        json_data = error.validation_error(
            ValidationError(messages="foobar"), pyramid_request
        )
        assert pyramid_request.response.status_code == 422
        assert json_data == {
            "message": "Unable to process the contained instructions",
            "details": "foobar",
        }


class TestCanvasAPIAccessTokenError:
    def test_it(self, pyramid_request):
        json_data = error.canvas_api_access_token_error(pyramid_request)

        assert pyramid_request.response.status_code == 400
        assert json_data == {"message": None, "details": None}


class TestCanvasAPIError:
    def test_it(self, pyramid_request):
        json_data = error.proxy_api_error(
            CanvasAPIError(explanation="test_explanation", details={"foo": "bar"}),
            pyramid_request,
        )

        assert pyramid_request.response.status_code == 400
        assert json_data == {
            "message": "test_explanation",
            "details": {"foo": "bar"},
        }


class TestLTIOutcomesAPIError:
    def test_it(self, pyramid_request):
        json_data = error.proxy_api_error(
            LTIOutcomesAPIError(explanation="test_explanation", details={"foo": "bar"}),
            pyramid_request,
        )

        assert pyramid_request.response.status_code == 400
        assert json_data == {
            "message": "test_explanation",
            "details": {"foo": "bar"},
        }


class TestNotFound:
    def test_it_sets_response_status(self, pyramid_request):
        error.notfound(pyramid_request)

        assert pyramid_request.response.status_int == 404

    def test_it_shows_a_generic_error_message_to_the_user(self, pyramid_request):
        result = error.notfound(pyramid_request)

        assert result["message"] == "Endpoint not found"


class TestForbidden:
    def test_it_sets_response_status(self, pyramid_request):
        error.forbidden(pyramid_request)

        assert pyramid_request.response.status_int == 403

    def test_it_shows_a_generic_error_message_to_the_user(self, pyramid_request):
        result = error.forbidden(pyramid_request)

        assert result["message"] == "You're not authorized to view this page"


class TestAPIError:
    def test_it(self, pyramid_request):
        json_data = error.api_error(pyramid_request)

        assert pyramid_request.response.status_code == 500
        assert json_data == {
            "message": "A problem occurred while handling this request. Hypothesis has been notified."
        }
