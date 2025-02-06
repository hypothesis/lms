import os

from pyramid.response import FileResponse
from pyramid.view import view_config


@view_config(route_name="favicon")
def favicon(request):
    here = os.path.dirname(__file__)  # noqa: PTH120
    icon = os.path.join(here, "..", "static", "images", "favicons", "favicon.ico")  # noqa: PTH118
    return FileResponse(icon, request=request)
