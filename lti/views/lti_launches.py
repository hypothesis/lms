from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pylti.common import verify_request_common
from lti.models import application_instance as ai

@view_config(route_name="lti_launches", renderer="json", request_method="POST")
def lti_launches(request):
  consumer_key = request.params["oauth_consumer_key"]
  instance = request.db.query(ai.ApplicationInstance).filter(
    ai.ApplicationInstance.consumer_key == consumer_key).one()

  consumers = {}

  consumers[consumer_key] = { "secret": instance.shared_secret }

  # TODO rescue from an invalid lti launch
  verify_request_common(consumers, request.url, request.method, dict(request.headers), dict(request.params))
  redirect_url = request.route_url("sixty_six")
  return HTTPFound(location=redirect_url)



