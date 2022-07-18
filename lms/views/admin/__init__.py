from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.renderers import render_to_response
from pyramid.view import forbidden_view_config, notfound_view_config, view_config

from lms.validation._exceptions import ValidationError


@forbidden_view_config(path_info="/admin/*")
def logged_out(request):
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
    return HTTPFound(location=request.route_url("admin.instances"))


def flash_validation(request, schema):
    try:
        schema(request).parse()
    except ValidationError as err:
        request.session.flash(err.messages["form"], "validation")
        return True
    return False


def error_render_to_response(
    request, error_message, template, template_args, flash_type="errors"
):
    request.session.flash(error_message, flash_type)
    response = render_to_response(template, template_args, request=request)
    response.status = 400
    return response
