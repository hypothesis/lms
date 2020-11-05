import pytest

from lms.services import CanvasAPIError, CanvasAPIPermissionError, LTIOutcomesAPIError
from lms.validation import ValidationError
from lms.views.api.exceptions import ExceptionViews


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


class TestCanvasAPIAccessTokenError:
    def test_it(self, pyramid_request, views):
        json_data = views.canvas_api_access_token_error()

        assert pyramid_request.response.status_code == 400
        assert json_data == {}


class TestCanvasAPIPermissionError:
    def test_it(self, context, pyramid_request, views):
        json_data = views.canvas_api_permission_error()

        assert pyramid_request.response.status_code == 400
        assert json_data == {
            "error_code": context.error_code,
            "details": context.details,
        }

    @pytest.fixture
    def context(self):
        return CanvasAPIPermissionError(details={"foo": "bar"})


class TestCanvasAPIError:
    def test_it(self, pyramid_request, views):
        json_data = views.proxy_api_error()

        assert pyramid_request.response.status_code == 400
        assert json_data == {
            "message": "test_explanation",
            "details": {"foo": "bar"},
        }

    @pytest.fixture
    def context(self):
        return CanvasAPIError(explanation="test_explanation", details={"foo": "bar"})


class TestLTIOutcomesAPIError:
    def test_it(self, pyramid_request, views):
        json_data = views.proxy_api_error()

        assert pyramid_request.response.status_code == 400
        assert json_data == {
            "message": "test_explanation",
            "details": {"foo": "bar"},
        }

    @pytest.fixture
    def context(self):
        return LTIOutcomesAPIError(
            explanation="test_explanation", details={"foo": "bar"}
        )


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


class TestAPIError:
    def test_it(self, pyramid_request, views):
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
    return ExceptionViews(context, pyramid_request)
