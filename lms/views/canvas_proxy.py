import jwt

from pyramid.view import view_config
from pyramid.response import Response
from lms.models import application_instance as ai
#from lms.users import find_by_lms_guid 
from lms.util.canvas_api import CanvasApi, GET
from lms.config.settings import env_setting
from lms.util.authenticate import authenticate 


# TODO
# * Add proxy api
#    * Add Jwts
#       * Where should jwts get stored
#    * Look up user from jwt
#
#Use http://niemeyer.net/mocker for mocking 

@authenticate
@view_config(route_name='canvas_proxy', renderer='json')
def canvas_proxy(request, decoded_jwt, user):
    # Request canvas files

#    canvas_api = CanvasApi(
#      new_token.access_token,
#      application_instance.lms_url
#    )
    
#    response = canvas_api.get_canvas_course_files(1773, {})
    import pdb; pdb.set_trace()

    return Response({
      'bad': True    
    }, status=200)
