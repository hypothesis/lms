"""Error views for the API."""
from pyramid import i18n
from pyramid.view import forbidden_view_config, notfound_view_config


_ = i18n.TranslationStringFactory(__package__)


@forbidden_view_config(path_info="/api/*", renderer="json")
def forbidden(request):
    request.response.status_int = 403
    return {"message": _("You're not authorized to view this page")}


@notfound_view_config(path_info="/api/*", renderer="json")
def notfound(request):
    request.response.status_int = 404
    return {"message": _("Endpoint not found")}
