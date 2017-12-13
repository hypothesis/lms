"""Provide a decorator that add lti validation capabilities to a pyramid view."""
import jwt
import pylti.common
from lms.models import application_instance as ai


def get_application_instance(db, consumer_key):
    return db.query(ai.ApplicationInstance).filter(
        ai.ApplicationInstance.consumer_key == consumer_key
    ).one()


def lti_launch(view_function):
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
        consumer_key = request.params["oauth_consumer_key"]
        instance = get_application_instance(request.db, consumer_key)

        consumers = {}

        consumers[consumer_key] = {"secret": instance.shared_secret}

        # TODO rescue from an invalid lms launch
        pylti.common.verify_request_common(consumers, request.url, request.method, dict(request.headers), dict(request.params))
        data = {'user_id': request.params['user_id'], 'roles': request.params['roles']}
        jwt_token = jwt.encode(data, request.registry.settings['jwt_secret'], 'HS256').decode('utf-8')
        return view_function(request, jwt_token)

    return wrapper
