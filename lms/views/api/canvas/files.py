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
from pyramid.view import view_config, view_defaults

from lms import util


@view_defaults(permission="canvas_api", renderer="json")
class FilesAPIViews:
    def __init__(self, request):
        self.request = request
        self.canvas_api_client = request.find_service(name="canvas_api_client")

    @view_config(request_method="GET", route_name="canvas_api.courses.files.list")
    def list_files(self):
        """Return the list of files in the given course."""
        return self.canvas_api_client.list_files(self.request.matchdict["course_id"])

    @view_config(request_method="GET", route_name="canvas_api.files.via_url")
    def via_url(self):
        """Return the Via URL for annotating the given Canvas file."""
        public_url = self.canvas_api_client.public_url(
            self.request.matchdict["file_id"]
        )
        via_url = util.via_url(self.request, public_url)
        return {"via_url": via_url}
