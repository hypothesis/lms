"""Provide a decorator that add lti validation capabilities to a pyramid view."""
import jwt
from pylti.common import verify_request_common
from lti.models import application_instance as ai
from lti.config.settings import env_setting


def lti_launch(view_function):
    """
    Handle the verification of an lti launch.

    You should add this decorator before (logically) the route decorator. For example:

    @view_config(...)
    @lti_launch
    def some_view(request):
    ...
    """
    def wrapper(request):
        """Handle the lti validation."""
        consumer_key = request.params["oauth_consumer_key"]
        instance = request.db.query(ai.ApplicationInstance).filter(
            ai.ApplicationInstance.consumer_key == consumer_key
        ).one()

        consumers = {}

        consumers[consumer_key] = {"secret": instance.shared_secret}

        # TODO rescue from an invalid lti launch
        verify_request_common(consumers, request.url, request.method, dict(request.headers), dict(request.params))
        data = {'user_id': request.params['user_id'], 'roles': request.params['roles']}
        jwt_token = jwt.encode(data, env_setting('JWT_SECRET'), 'HS256').decode('utf-8')
        return view_function(request, jwt)

    return wrapper
