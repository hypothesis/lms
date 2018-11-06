from pyramid.httpexceptions import HTTPBadRequest

from lms import models


def lti_params_for(request):
    """
    Return the LTI params for the given request.

    If the request is an LTI launch request then just return request.params.

    If the request is an OAuth 2.0 redirect request then use the request's
    `state` param to retrieve the launch params that were previously stashed in
    the DB and return them.

    :raise HTTPBadRequest: if the request is an OAuth redirect but no
      associated launch params can be found in the DB

    """
    if "state" in request.params:
        # This is an OAuth redirect request, not an LTI launch request.
        # Retrieve the LTI launch params from the database instead of using
        # request.params directly.
        lti_params = models.find_lti_params(request.db, request.params["state"])
        if lti_params is None:
            raise HTTPBadRequest("OAuth state was not found")
        return lti_params

    # This is an LTI launch request.
    return request.params
