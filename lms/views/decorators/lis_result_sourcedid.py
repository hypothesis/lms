"""View decorators for working with LISResultSourcedId data."""

import functools

from lms.views.helpers import is_instructor
from lms.validation import LISResultSourcedIdSchema, ValidationError

__all__ = ["upsert_lis_result_sourcedid"]


def upsert_lis_result_sourcedid(wrapped):
    """Create or update a record of LIS result/outcome data for a student launch."""

    @functools.wraps(wrapped)
    def wrapper(context, request):
        try:
            lis_result_sourcedid = LISResultSourcedIdSchema(
                request
            ).lis_result_sourcedid_info()
        except ValidationError:
            # We're missing something we need in the request.
            # This can happen if the user is not a student, or if the needed
            # LIS data is not present on the request.
            return wrapped(context, request)

        if (
            request.lti_user.is_instructor
            or lis_result_sourcedid.tool_consumer_info_product_family_code
            != "BlackboardLearn"
        ):
            # Don't create records for instructors, or for LMSes other than
            # BlackboardLearn (at least for now)
            return wrapped(context, request)

        lis_result_svc = request.find_service(name="lis_result_sourcedid")
        lis_result_svc.upsert(
            lis_result_sourcedid, h_user=context.h_user, lti_user=request.lti_user
        )
        return wrapped(context, request)

    return wrapper
