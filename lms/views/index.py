from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config


@view_config(route_name="welcome")
@view_config(route_name="index")
def index(_):
    """Redirect curious users to some help."""

    return HTTPFound(
        location="https://web.hypothes.is/help/installing-the-hypothesis-lms-app/"
    )
