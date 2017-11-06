from pyramid.renderers import render_to_response
from pylti.common import verify_request_common
from lti.models import application_instance as ai

def lti_launch(view_function):
  """
    This decorator handle the verification of an lti launch and can be used to decorate a route.
    You should add this decorator before (logically) the route decorator. For example:

    @view_config(...)
    @lti_launch
    def some_view(request):
      ...
  """

  def wrapper(request):
    consumer_key = request.params["oauth_consumer_key"]
    instance = request.db.query(ai.ApplicationInstance).filter(
    ai.ApplicationInstance.consumer_key == consumer_key).one()

    consumers = {}

    consumers[consumer_key] = { "secret": instance.shared_secret }

    # TODO rescue from an invalid lti launch
    verify_request_common(consumers, request.url, request.method, dict(request.headers), dict(request.params))
    return view_function(request)

  return wrapper

def view_renderer(renderer):
  def view_decorator(view_function):
    def wrapper(request, **kwargs):
      return render_to_response(
        renderer,
        view_function(request, **kwargs),
        request=request
      )
    return wrapper
  return view_decorator


