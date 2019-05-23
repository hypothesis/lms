"""View decorators for reporting to the ``/reports`` page."""
import datetime

from lms.models.lti_launches import LtiLaunches


def report_lti_launch(wrapped):
    """
    Report an LTI launch to the ``/reports`` page.

    This decorator assumes that it's only used on LTI launch views.
    """

    def wrapper(context, request):
        request.db.add(
            LtiLaunches(
                context_id=request.params.get("context_id"),
                lti_key=request.params.get("oauth_consumer_key"),
                created=datetime.datetime.utcnow(),
            )
        )
        return wrapped(context, request)

    return wrapper
