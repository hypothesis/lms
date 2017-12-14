from urllib.parse import urlparse, parse_qs
from pyramid.response import Response
from lms.util.canvas_api import canvas_api
from lms.models.users import User
from lms.models.application_instance import build_from_lms_url
from lms.models.oauth_state import find_by_state
import json


@canvas_api
def view_function(request, decoded_jwt, user, canvas_api):
    return Response("<h1>Howdy</h1>")

class TestCanvasApi(object):
    """Test the associate user decorator"""
    def test_it_creates_canvas_api(self, canvas_api_proxy):
        response = view_function(canvas_api_proxy['request'],
                     canvas_api_proxy['decoded_jwt'],
                     canvas_api_proxy['user'])

        import pdb; pdb.set_trace()
        assert response.code == 302
        assert "https://hypothesis.instructure.com/login/oauth2/auth" in response.location

#   def test_it_handles_no_token():
#   def test_it_handles_no_application_instance():



