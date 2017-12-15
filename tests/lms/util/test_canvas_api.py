from urllib.parse import urlparse, parse_qs
from pyramid.response import Response
from lms.util.canvas_api import canvas_api
from lms.models.users import User
from lms.models.application_instance import build_from_lms_url
from lms.models.oauth_state import find_by_state

import json


def build_mock_view(assertions):
    @canvas_api
    def view_function(request, decoded_jwt, user, canvas_api):
        assertions(request, decoded_jwt, user, canvas_api)
        return Response("<h1>Howdy</h1>")
    return view_function

class TestCanvasApi(object):
    def test_it_creates_canvas_api(self, canvas_api_proxy):
        def assertions(request, decoded_jwt, user, canvas_api):
            assert canvas_api.canvas_token == canvas_api_proxy['token'].access_token
            assert canvas_api_proxy['application_instance'].lms_url == canvas_api.canvas_domain
        response = build_mock_view(assertions)(
                                  canvas_api_proxy['request'],
                                  canvas_api_proxy['decoded_jwt'],
                                  canvas_api_proxy['user'])

    def test_it_handles_no_user(self, canvas_api_proxy):
        def assertions(request, decoded_jwt, user, canvas_api):
            pass
        response = build_mock_view(assertions)(
                                  canvas_api_proxy['request'],
                                  canvas_api_proxy['decoded_jwt'],
                                  None)
        assert response.status_code == 404
        
    def test_it_handles_no_token(self, canvas_api_proxy):
        def assertions(request, decoded_jwt, user, canvas_api):
            pass
        request = canvas_api_proxy['request']
        token = canvas_api_proxy['token']
        request.db.delete(token)
        response = build_mock_view(assertions)(
                                  canvas_api_proxy['request'],
                                  canvas_api_proxy['decoded_jwt'],
                                  canvas_api_proxy['user'])
        assert response.status_code == 404
    def test_it_handles_no_application_instance(self, canvas_api_proxy):
        def assertions(request, decoded_jwt, user, canvas_api):
            pass
        request = canvas_api_proxy['request']
        application_instance = canvas_api_proxy['application_instance']
        request.db.delete(application_instance)
        response = build_mock_view(assertions)(
                                  canvas_api_proxy['request'],
                                  canvas_api_proxy['decoded_jwt'],
                                  canvas_api_proxy['user'])
        assert response.status_code == 404


