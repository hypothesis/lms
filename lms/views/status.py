import logging

from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.view import view_config

LOG = logging.getLogger(__name__)


@view_config(route_name="status", renderer="json")
def status(request):
    try:
        request.db.execute("SELECT 1")
        return {"status": "okay"}
    except Exception as err:
        LOG.exception("Executing a simple database query failed:")
        raise HTTPInternalServerError("Database connection failed") from err
