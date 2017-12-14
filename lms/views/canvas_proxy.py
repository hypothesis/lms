import jwt

from pyramid.view import view_config
from pyramid.response import Response
from lms.models.application_instance import find_by_oauth_consumer_key
from lms.models.tokens import find_token_by_user_id
from lms.util.canvas_api import CanvasApi, GET
from lms.config.settings import env_setting
from lms.util.authenticate import authenticate


@view_config(route_name='canvas_proxy', request_method='POST', renderer='json')
@authenticate
def canvas_proxy(request, decoded_jwt, user):
    token = find_token_by_user_id(request.db, user.id)
    consumer_key = decoded_jwt['consumer_key']
    application_instance = find_by_oauth_consumer_key(request.db, consumer_key)

    if token is None or application_instance is None:
        pass # TODO throw error

    canvas_api = CanvasApi(
      token.access_token,
      application_instance.lms_url
    )

    result = canvas_api.proxy(
             f'/api/v1/{request.params['endpoint_url']}',
             request.params['method'],
             request.params['params'])
    return Response(result.json(), status=response.status_code)
