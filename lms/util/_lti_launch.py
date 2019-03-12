"""Decorator that add lti validation capabilities to a pyramid view."""
from functools import wraps

from lms.util.jwt import build_jwt_from_lti_launch


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
        request.find_service(name="lti").verify_launch_request()

        jwt_secret = request.registry.settings["jwt_secret"]
        jwt_token = build_jwt_from_lti_launch(request.params, jwt_secret)

        return view_function(request, jwt_token)

    return wrapper
