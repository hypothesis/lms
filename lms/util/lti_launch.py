"""Provide a decorator that add lti validation capabilities to a pyramid view."""
import jwt
import pylti.common
from lms.models import application_instance as ai
from lms.config.settings import env_setting


def get_application_instance(session, consumer_key):
    """Find an application instance from the application consumer key"""
    return session.query(ai.ApplicationInstance).filter(
        ai.ApplicationInstance.consumer_key == consumer_key
    ).one()


def default_get_secret(request, consumer_key):
    """
    Default method to retrieve the lti secret given the current request and
    the application consumer key
    """
    instance = get_application_instance(request.db, consumer_key)
    return instance.shared_secret

def default_get_lti_launch_params(request):
    """
    Default method to retrieve the lti launch params given the current request
    """
    return dict(request.params)

def lti_launch(get_lti_launch_params=default_get_lti_launch_params,
               get_secret=default_get_secret):
    """
    Initialize decorator with methods to customize extracting lti launch
    params and retrieving lti secret
    """
    def decorator(view_function):
        """
        Handle the verification of an lms launch.

        You should add this decorator before (logically) the route decorator. For example:

        @view_config(...)
        @lti_launch
        def some_view(request):
        ...
        """
        def wrapper(request):
            """Handle the lms validation."""
            lti_params = get_lti_launch_params(request)
            consumer_key = lti_params['oauth_consumer_key']
            shared_secret = get_secret(request, consumer_key)

            consumers = {}

            consumers[consumer_key] = {"secret": shared_secret}
            # TODO rescue from an invalid lms launch
            pylti.common.verify_request_common(
                consumers,
                request.url,
                request.method,
                dict(request.headers),
                dict(lti_params))
            data = {'user_id': lti_params['user_id'], 'roles': lti_params['roles']}
            jwt_token = jwt.encode(data, env_setting('JWT_SECRET'), 'HS256').decode('utf-8')
            return view_function(request, jwt_token)
        return wrapper
    return decorator
