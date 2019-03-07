"""Decorator that add lti validation capabilities to a pyramid view."""
from functools import wraps

import pylti.common

from lms.models import application_instance as ai
from lms.util.jwt import build_jwt_from_lti_launch
from lms.exceptions import MissingLTILaunchParamError


def get_application_instance(db, consumer_key):
    """
    Return the application instance with the given ``consumer_key``.

    :arg db: the sqlalchemy session
    :arg consumer_key: the consumer key to search for
    :type consumer_key: str

    :raise sqlalchemy.orm.exc.NoResultFound: if there's no application instance
      in the DB with the given ``consumer_key``
    :raise sqlalchemy.orm.exc.MultipleResultsFound: if there's more than one
      application instance in the DB with the given ``consumer_key``

    :return: the matching application instance
    :rtype: lms.models.ApplicationInstance
    """
    return (
        db.query(ai.ApplicationInstance)
        .filter(ai.ApplicationInstance.consumer_key == consumer_key)
        .one()
    )


def get_lti_launch_params(request):
    """Retrieve the LTI launch params."""
    return dict(request.params)


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
        lti_params = get_lti_launch_params(request)
        try:
            consumer_key = lti_params["oauth_consumer_key"]
        except KeyError:
            raise MissingLTILaunchParamError("oauth_consumer_key")

        shared_secret = get_application_instance(request.db, consumer_key).shared_secret

        consumers = {}

        consumers[consumer_key] = {"secret": shared_secret}
        # TODO rescue from an invalid lms launch
        pylti.common.verify_request_common(
            consumers,
            request.url,
            request.method,
            dict(request.headers),
            dict(lti_params),
        )
        jwt_secret = request.registry.settings["jwt_secret"]
        jwt_token = build_jwt_from_lti_launch(request.params, jwt_secret)
        return view_function(request, jwt_token)

    return wrapper
