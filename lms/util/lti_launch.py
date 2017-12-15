"""Decorator that add lti validation capabilities to a pyramid view."""
import pylti.common
from lms.models import application_instance as ai
from lms.util.jwt import build_jwt_from_lti_launch


def get_application_instance(session, consumer_key):
    """Find an application instance from the application consumer key."""
    return session.query(ai.ApplicationInstance).filter(
        ai.ApplicationInstance.consumer_key == consumer_key
    ).one()


def default_get_secret(request, consumer_key):
    """Retrieve the lti secret given."""
    instance = get_application_instance(request.db, consumer_key)
    return instance.shared_secret


def default_get_lti_launch_params(request):
    """Retrieve the lti launch params."""
    return dict(request.params)


def lti_launch(get_lti_launch_params=default_get_lti_launch_params,
               get_secret=default_get_secret):
    """
    Initialize decorator.

    Allow caller to supply methods to customize extracting lti launch
    params and retrieving lti secret
    """
    def decorator(view_function):
        """
        Handle the verification of an lms launch.

        You should add this decorator before (logically) the route decorator.
        For example:

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
            jwt_secret = request.registry.settings['jwt_secret']
            jwt_token = build_jwt_from_lti_launch(request.params, jwt_secret)
            return view_function(request, jwt_token)
        return wrapper
    return decorator
