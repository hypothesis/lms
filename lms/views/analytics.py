from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.validation.authentication import BearerTokenSchema


@view_config(
    request_method="POST",
    renderer="json",
    route_name="lti.analytics.assignment",
    permission=Permissions.API,
)
def assignment_from_launch(request):
    response = HTTPFound(
        location=request.route_url("analytics.assignment"),
    )
    auth_token = BearerTokenSchema(request).authorization_param(request.lti_user)
    # This cookie, in chrome, ends up in a CHIP for the LMS
    # Is that important? While testing this I'm using link that opens in the same window.
    # Maybe irrelevant if if opened in a new window?
    response.set_cookie(
        "authorization",
        value=auth_token,
        secure=True,  # not request.registry.settings["dev"] instead?
        httponly=True,  # True? Not sure
        samesite="none",  # True? Not sure
    )
    return response


@view_config(
    request_method="GET",
    renderer="json",
    route_name="analytics.assignment",
    permission=Permissions.API,
)
def assignment(request):
    # return JSConfig with pointer to the API
    # This config should probably also include the API token again
    # so this is the only view that will use the cooke based token
    # return {"display_name": request.lti_user.display_name, "Cookie": "set 👍"}

    # TO make testing this easier I'm redirecting to the API endpoint
    lti_user = request.lti_user
    assignment_service = request.find_service(name="assignment")

    assignment = assignment_service.get_assignment(
        lti_user.tool_consumer_instance_guid, lti_user.lti.assignment_id
    )
    return HTTPFound(
        location=request.route_url("analytics.assignment.api", id_=assignment.id),
    )


@view_config(
    request_method="GET",
    renderer="json",
    route_name="analytics.assignment.api",
    permission=Permissions.API,
)
def assignment_api(request):
    print("API ENDPOING")
    lti_user = request.lti_user
    settings = request.registry.settings
    authority = settings["h_authority"]

    # With Permissions.API we know we have a valid token
    # but that token is coming from a launch so is scoped to one course/assignment
    # we want the cookie to be valid to navigate between different course/assignment stats so we have to broad that scope

    # We'll trust the info in our DB which we know is based on the info from the LMS after successful launches.
    # This information never expired so we'll use a time limit

    import random
    from datetime import datetime, timedelta

    from lms.models import Assignment, AssignmentMembership, User

    # This might be an edge cases but currently in our system one LMS user might map to many DB users in different installs.
    # Get all the equivalent ones
    db = request.db

    assignment_id = request.matchdict["id_"]

    query = (
        db.query(Assignment)
        .join(AssignmentMembership)
        .join(User)
        .filter(
            # These users are equivalent because they have the same H userid
            User.h_userid == lti_user.h_user.userid(authority),
            Assignment.id == assignment_id,
            # This information never expired so we'll use a time limit
            # Alternatively we could fetch the courses roster every so often and use that info but that an extra piece of work
            # AssignmentMembership.updated >= datetime.now() - timedelta(days=30),
        )
    )
    # TODO We also have to check the user is a user on that course
    assignment = query.one_or_none()
    if not assignment:
        # Should we able to tell 404s (the assignment doesn't exists) vs 403 you don't have access to it   ?
        # It probalby make sense to display a better error message
        return "404"

    # return JSConfig with pointer to the API
    return {
        "display_name": request.lti_user.display_name,
        "assignment": assignment.title,
        "analytics": random.randint(0, 100),
    }
