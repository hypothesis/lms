import json
from pyramid.view import view_config
from pyramid.response import Response
from lms.util.authenticate import authenticate
from lms.util.canvas_api import canvas_api as canvas_api_provider


@view_config(route_name='canvas_proxy', request_method='POST')
@authenticate
@canvas_api_provider
def canvas_proxy(request, _decoded_jwt, canvas_api, **_):
    """
    Route to support proxying client side XHR requests.

    We can't send the canvas token obtained through the oauth process
    to the client side application, so we must proxy requets through
    this view to add the canvas token before requests reach canvas
    """
    result = canvas_api.proxy(
        f"/api/v1/{request.json['endpoint_url']}",
        request.json['method'],
        request.json['params'])
    response = None
    try:
        response = json.dumps(result.json())
    except ValueError:
        response = result.text()
    return Response(response, status=result.status_code)
