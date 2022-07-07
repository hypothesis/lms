from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import forbidden_view_config, notfound_view_config, view_config

from lms.validation._exceptions import ValidationError


@forbidden_view_config(path_info="/admin/*")
def logged_out(request):
    return HTTPFound(location=request.route_url("pyramid_googleauth.login"))


@notfound_view_config(path_info="/admin/*", append_slash=True)
def notfound(_request):
    return HTTPNotFound()


@view_config(route_name="admin.index")
def index(request):
    return HTTPFound(location=request.route_url("admin.instances"))


def flash_validation(request, schema):
    try:
        schema(request).parse()
    except ValidationError as err:
        request.session.flash(err.messages["form"], "validation")
        return True

    return False
