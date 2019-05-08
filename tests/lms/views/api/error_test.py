from lms.views.api import error


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
