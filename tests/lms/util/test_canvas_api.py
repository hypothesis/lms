# pylint: disable=no-value-for-parameter
from pyramid.response import Response
from lms.util import canvas_api


def build_mock_view(assertions):
    @canvas_api
    def view_function(request, decoded_jwt, user, canvas_api):
        assertions(request, decoded_jwt, user, canvas_api)
        return Response("<h1>Howdy</h1>")
    return view_function


class TestCanvasApi:
    def test_it_creates_canvas_api(self, canvas_api_proxy):
        def assertions(_request, _decoded_jwt, _user, canvas_api):
            assert canvas_api.canvas_token == canvas_api_proxy['token'].access_token
            assert canvas_api_proxy['application_instance'].lms_url == canvas_api.canvas_domain
        build_mock_view(assertions)(
            canvas_api_proxy['request'],
            canvas_api_proxy['decoded_jwt'],
            canvas_api_proxy['user']
        )

    def test_it_handles_no_user(self, canvas_api_proxy):
        def assertions(_request, _decoded_jwt, _user, _canvas_api):
            pass
        response = build_mock_view(assertions)(
            canvas_api_proxy['request'],
            canvas_api_proxy['decoded_jwt'],
            None
        )
        assert response.status_code == 404

    def test_it_handles_no_token(self, canvas_api_proxy):
        def assertions(_request, _decoded_jwt, _user, _canvas_api):
            pass

        request = canvas_api_proxy['request']
        token = canvas_api_proxy['token']
        request.db.delete(token)
        response = build_mock_view(assertions)(
            canvas_api_proxy['request'],
            canvas_api_proxy['decoded_jwt'],
            canvas_api_proxy['user']
        )
        assert response.status_code == 404

    def test_it_handles_no_application_instance(self, canvas_api_proxy):
        def assertions(_request, _decoded_jwt, _user, _canvas_api):
            pass
        request = canvas_api_proxy['request']
        application_instance = canvas_api_proxy['application_instance']
        request.db.delete(application_instance)
        response = build_mock_view(assertions)(
            canvas_api_proxy['request'],
            canvas_api_proxy['decoded_jwt'],
            canvas_api_proxy['user']
        )
        assert response.status_code == 404
