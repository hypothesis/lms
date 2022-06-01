from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import forbidden_view_config, notfound_view_config, view_config


@forbidden_view_config(path_info="/admin/*")
def logged_out(request):
    return HTTPFound(location=request.route_url("pyramid_googleauth.login"))


@notfound_view_config(path_info="/admin/*", append_slash=True)
def notfound(_request):
    return HTTPNotFound()


@view_config(route_name="admin.index")
def index(request):
    return HTTPFound(location=request.route_url("admin.instances"))


def flash_missing_fields(request, fields):
    missing_fields = [field for field in fields if not request.params.get(field)]
    if missing_fields:
        is_plural = len(missing_fields) > 1
        request.session.flash(
            f"{', '.join(missing_fields)} {'are' if is_plural else 'is'} required",
            "errors",
        )
        return True

    return False
