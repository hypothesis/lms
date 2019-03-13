"""Decorator that add lti validation capabilities to a pyramid view."""
from functools import wraps

import pylti.common

from lms.util.jwt import build_jwt_from_lti_launch
from lms.exceptions import MissingLTILaunchParamError


def lti_launch(view_function):
    """
    Handle the verification of an lms launch.

    You should add this decorator before (logically) the route decorator.
    For example:

    @view_config(...)
    @lti_launch
    def some_view(request):
    ...
    """

    @wraps(view_function)
    def wrapper(request):
        """Handle the lms validation."""
        try:
            consumer_key = request.params["oauth_consumer_key"]
        except KeyError:
            raise MissingLTILaunchParamError("oauth_consumer_key")

        shared_secret = request.find_service(name="ai_getter").shared_secret(
            consumer_key
        )

        consumers = {}

        consumers[consumer_key] = {"secret": shared_secret}
        # TODO rescue from an invalid lms launch
        pylti.common.verify_request_common(
            consumers,
            request.url,
            request.method,
            dict(request.headers),
            dict(request.params),
        )
        jwt_secret = request.registry.settings["jwt_secret"]
        jwt_token = build_jwt_from_lti_launch(request.params, jwt_secret)
        return view_function(request, jwt_token)

    return wrapper
