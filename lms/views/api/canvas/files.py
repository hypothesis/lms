"""
Proxy API for Canvas's Files API.

Gives our frontend code access to Canvas's Files API:
https://canvas.instructure.com/doc/api/files.html

Requests to this proxy API are authenticated using this app's authentication
policies (for example: a JWT in an ``Authorization`` header) and this API
therefore knows what LTI user is making the request. This API then makes
server-to-server requests, authenticated using OAuth 2 access tokens, to the
appropriate Canvas instance's files API and returns the results to the original
proxy API caller::

                         +---------+
                         | Browser |
                         +---------+
                         |         ↑
    1. List files request|         |
       (JWT auth)        |         |4. Proxied list files response
                         ↓         |
                        +-----------+
                        | Proxy API |
                        +-----------+
                         |         ↑
    2. Proxied list files|         |
       request (OAuth 2) |         |3. List files response
                         ↓         |
                      +---------------+
                      |Real Canvas API|
                      +---------------+
"""
from pyramid.view import view_config


@view_config(
    permission="canvas_api",
    renderer="json",
    request_method="GET",
    route_name="canvas_api.courses.files.list",
)
def list_files(request):
    """Return the list of files in the given course."""
    course_id = request.matchdict["course_id"]
    canvas_api_client = request.find_service(name="canvas_api_client")
    return canvas_api_client.list_files(course_id)


@view_config(
    permission="canvas_api",
    renderer="json",
    request_method="GET",
    route_name="canvas_api.files.public_url",
)
def public_url(_request):
    """Return the public URL of the given file."""
    # TODO: Replace the hardcoded URL with a real one received from Canvas.
    return {
        "public_url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    }
