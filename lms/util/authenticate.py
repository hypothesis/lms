"""Decorate routes with the ability to authenticate requests."""
import jwt
from pyramid.response import Response


def authenticate(view_function):
    """Wrap a view function with with JWT authentication."""
    def wrapper(request):
        """Validate the JWT signature."""
        try:
            decoded_jwt = jwt.decode(request.params['jwt_token'],
                    request.registry.settings['jwt_secret'], algorithms=['HS256'])
        except (jwt.exceptions.DecodeError, KeyError):
            return Response('<p>Error: Unauthenticated Request</p>')

        return view_function(request, decoded_jwt)
    return wrapper
