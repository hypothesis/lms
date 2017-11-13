"""Decorate routes with the ability to authenticate requests."""
import jwt
from lms.config.settings import env_setting
from pyramid.response import Response


def authenticate(view_function):
    """Wrap a view function with with JWT authentication."""
    def wrapper(request):
        """Validate the JWT signature."""
        try:
            decoded_jwt = jwt.decode(request.params['jwt'], env_setting('JWT_SECRET'), algorithms=['HS256'])
            return view_function(request, decoded_jwt)
        except (jwt.exceptions.DecodeError, KeyError):
            return Response('<p>Error: Unauthenticated Request</p>')

    return wrapper
