import os

from pyramid.response import FileResponse
from pyramid.view import view_config


@view_config(route_name="favicon")
def favicon(request):
    here = os.path.dirname(__file__)
    icon = os.path.join(here, "..", "static", "images", "favicons", "favicon.ico")
    return FileResponse(icon, request=request)
