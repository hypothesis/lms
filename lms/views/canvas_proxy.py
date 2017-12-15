import jwt

from pyramid.view import view_config
from pyramid.response import Response
from lms.util.authenticate import authenticate
from lms.util.canvas_api import canvas_api

@view_config(route_name='canvas_proxy', request_method='POST', renderer='json')
@authenticate
@canvas_api
def canvas_proxy(request, decoded_jwt, user, canvas_api):
    result = canvas_api.proxy(
             f'/api/v1/{request.params['endpoint_url']}',
             request.params['method'],
             request.params['params'])
    return Response(result.json(), status=response.status_code)
