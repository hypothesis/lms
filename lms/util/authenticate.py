"""Decorate routes with the ability to authenticate requests."""
import jwt
from pyramid.response import Response
from lms.models.users import find_by_lms_guid
from lms.models.application_instance import find_by_oauth_consumer_key


def authenticate(view_function):
    """Wrap a view function with with JWT authentication."""
    def wrapper(request):
        """Validate the JWT signature."""
        try:
            jwt_token = None
            if 'Authorization' in request.headers:
                jwt_token = request.headers['Authorization']
            else:
                jwt_token = request.params['jwt_token']
            decoded_jwt = jwt.decode(
                                    jwt_token,
                                    request.registry.settings['jwt_secret'],
                                    algorithms=['HS256'])

            lms_guid = decoded_jwt['user_id']
            consumer_key = decoded_jwt['consumer_key']
            user = find_by_lms_guid(request.db, lms_guid)

        except (jwt.exceptions.DecodeError, KeyError):
            return Response('<p>Error: Unauthenticated Request</p>', status=401)
        return view_function(request, decoded_jwt, user=user)
    return wrapper
