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
def list_files(_request):
    """Return the list of files in the given course."""
    # TODO: Replace this stub response with a real response based on a response
    # obtained from the Canvas API.
    return [
        {
            "id": 56,
            "display_name": "Biography.pdf",
            "updated_at": "2017-03-06T12:58:27Z",
        },
        {"id": 1, "display_name": "Comedies.pdf", "updated_at": "2012-05-01T20:36:32Z"},
        {
            "id": 23,
            "display_name": "Histories.pdf",
            "updated_at": "2011-011-20T07:23:20Z",
        },
        {"id": 460, "display_name": "Poems.pdf", "updated_at": "2018-08-17T11:45:50Z"},
        {"id": 7, "display_name": "Sonnets.pdf", "updated_at": "2016-06-06T17:58:01"},
        {
            "id": 112,
            "display_name": "Tragedies.pdf",
            "updated_at": "2010-07-23T14:01:50Z",
        },
    ]
