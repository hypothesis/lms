from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import forbidden_view_config, notfound_view_config, view_config

from lms.validation._exceptions import ValidationError


@forbidden_view_config(path_info="/admin/*")
def forbidden(request):
    if request.identity and request.identity.userid:
        # Logged in but missing permissions, go back to the admin page's index.
        request.session.flash(
            f"You don't have permissions for that: {request.path}", "errors"
        )
        return HTTPFound(location=request.route_url("admin.index"))

    # Not logged in, redirect to Google auth.
    return HTTPFound(
        location=request.route_url(
            "pyramid_googleauth.login", _query={"next": request.url}
        ),
    )


@notfound_view_config(path_info="/admin/*", append_slash=True)
def notfound(_request):
    return HTTPNotFound()


@view_config(route_name="admin.index")
def index(request):
    return HTTPFound(location=request.route_url("admin.instance.search"))


def flash_validation(request, schema):
    try:
        schema(request).parse()
    except ValidationError as err:
        request.session.flash(err.messages["form"], "validation")
        return True
    return False
