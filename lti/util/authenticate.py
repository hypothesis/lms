"""This module handles decorating routes with the ability to authenticate requests"""
import jwt
from lti.config.settings import env_setting
from pyramid.response import Response

def authenticate(view_function):
    """Takes a view function and wraps with with JWT authentication"""
    def wrapper(request):
        """Before doing anything the JWT signature will be validated"""
        try:
            decoded_jwt = jwt.decode(request.params['jwt'], env_setting('JWT_SECRET'), algorithms=['HS256'])
            return view_function(request, decoded_jwt)
        except (jwt.exceptions.DecodeError, KeyError):
            return Response('<p>Error: Unauthenticated Request</p>')

    return wrapper
