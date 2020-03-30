Canvas Proxy API
================

This package implements a proxy API for the Canvas API, giving our frontend
code access to the Canvas API:

https://canvas.instructure.com/doc/api/

Requests to this proxy API are authenticated using this app's authentication
policies (for example: a JWT in an `Authorization` header) and this API
therefore knows what LTI user is making the request. This API then makes
server-to-server requests, authenticated using OAuth 2 access tokens, to the
appropriate Canvas instance's files API and returns the results to the original
proxy API caller:

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
