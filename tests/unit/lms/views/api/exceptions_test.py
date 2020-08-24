import pytest
from h_matchers import Any
from pyramid.urldispatch import Route

from lms.services import CanvasAPIError, LTIOutcomesAPIError
from lms.validation import ValidationError
from lms.views.api.exceptions import ExceptionViews


class AuthURLTests:
    """Test for the "auth_url" in error responses, which apply to all error views."""

    def test_it_returns_the_Canvas_auth_URL_for_Canvas_API_requests(
        self, canvas_api_request, view
    ):
        json_data = view()

        assert json_data["auth_url"] == canvas_api_request.route_url(
            "canvas_api.authorize"
        )

    @pytest.mark.usefixtures("lti_api_request")
    def test_it_doesnt_retutn_an_auth_URL_for_LTI_API_requests(self, view):
        json_data = view()

        assert "auth_url" not in json_data

    @pytest.fixture
    def canvas_api_request(self, pyramid_request):
        pyramid_request.matched_route.name = "canvas_api.something"
        return pyramid_request

    @pytest.fixture
    def lti_api_request(self, pyramid_request):
        pyramid_request.matched_route.name = "lti_api.something"
        return pyramid_request


class TestSchemaValidationError(AuthURLTests):
    def test_it(self, pyramid_request, view):
        json_data = view()

        assert pyramid_request.response.status_code == 422
        assert json_data == Any.dict.containing(
            {
                "message": "Unable to process the contained instructions",
                "details": "foobar",
            }
        )

    @pytest.fixture
    def context(self):
        return ValidationError(messages="foobar")

    @pytest.fixture
    def view(self, views):
        return views.validation_error


class TestCanvasAPIAccessTokenError(AuthURLTests):
    def test_it(self, pyramid_request, view):
        json_data = view()

        assert pyramid_request.response.status_code == 400
        assert json_data == Any.dict.containing({"message": None, "details": None,})

    @pytest.fixture
    def view(self, views):
        return views.canvas_api_access_token_error


class TestCanvasAPIError(AuthURLTests):
    def test_it(self, pyramid_request, view):
        json_data = view()

        assert pyramid_request.response.status_code == 400
        assert json_data == Any.dict.containing(
            {"message": "test_explanation", "details": {"foo": "bar"},}
        )

    @pytest.fixture
    def context(self):
        return CanvasAPIError(explanation="test_explanation", details={"foo": "bar"})

    @pytest.fixture
    def view(self, views):
        return views.proxy_api_error


class TestLTIOutcomesAPIError(AuthURLTests):
    def test_it(self, pyramid_request, view):
        json_data = view()

        assert pyramid_request.response.status_code == 400
        assert json_data == Any.dict.containing(
            {"message": "test_explanation", "details": {"foo": "bar"},}
        )

    @pytest.fixture
    def context(self):
        return LTIOutcomesAPIError(
            explanation="test_explanation", details={"foo": "bar"}
        )

    @pytest.fixture
    def view(self, views):
        return views.proxy_api_error


class TestNotFound(AuthURLTests):
    def test_it(self, pyramid_request, view):
        json_data = view()

        assert pyramid_request.response.status_int == 404
        assert json_data == Any.dict.containing({"message": "Endpoint not found",})

    @pytest.fixture
    def view(self, views):
        return views.notfound


class TestForbidden(AuthURLTests):
    def test_it(self, pyramid_request, view):
        json_data = view()

        assert pyramid_request.response.status_int == 403
        assert json_data == Any.dict.containing(
            {"message": "You're not authorized to view this page",}
        )

    @pytest.fixture
    def view(self, views):
        return views.forbidden


class TestAPIError(AuthURLTests):
    def test_it(self, pyramid_request, view):
        json_data = view()

        assert pyramid_request.response.status_code == 500
        assert json_data == Any.dict.containing(
            {
                "message": (
                    "A problem occurred while handling this request. Hypothesis has"
                    " been notified."
                ),
            }
        )

    @pytest.fixture
    def view(self, views):
        return views.api_error


@pytest.fixture
def context():
    return None


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.matched_route = Route("route_name", "route_pattern")
    return pyramid_request


@pytest.fixture
def views(context, pyramid_request):
    return ExceptionViews(context, pyramid_request)
