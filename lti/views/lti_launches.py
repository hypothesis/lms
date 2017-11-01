from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pylti.common import verify_request_common

@view_config(route_name="lti_launches", renderer="json", request_method="POST")
def lti_launches(request):
  # TODO obviously this should not be hard coded
  consumers = {
    "hypothesis": {
      "secret": "fake_secret"
    }
  }

  # TODO rescue from an invalid lti launch
  verify_request_common(consumers, request.url, request.method, dict(request.headers), dict(request.params))
  redirect_url = request.route_url("sixty_six")
  return HTTPFound(location=redirect_url)



