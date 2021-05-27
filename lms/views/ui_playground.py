from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import notfound_view_config, view_config


@view_config(
    route_name="ui-playground", renderer="lms:templates/ui-playground.html.jinja2"
)
def ui_playground(_request):
    return {}


@notfound_view_config(path_info="/ui-playground", append_slash=True)
def notfound(_request):
    return HTTPNotFound()
