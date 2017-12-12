from pyramid.view import view_config
from pyramid.response import Response
from lms.models import application_instance as ai
from lms.util.canvas_api import CanvasApi, GET

# TODO
# * Add proxy api
#    * Add Jwts
#       * Where should jwts get stored
#    * Look up user from jwt
#
#Use http://niemeyer.net/mocker for mocking 
@view_config(route_name='canvas_proxy', renderer='json')
def canvas_proxy(request):
    # Request canvas files
#    canvas_api = CanvasApi(
#      new_token.access_token,
#      application_instance.lms_url
#    )

    response = canvas_api.get_canvas_course_files(1773, {})
    return Response({
      'bad': True    
    }, status=200)
