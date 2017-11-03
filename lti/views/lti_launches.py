from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from lti.util.lti_launch import lti_launch

@view_config(route_name='lti_launches', renderer='lti:templates/lti_launches/create_lti_launch.html.jinja2', request_method='POST')
@lti_launch
def lti_launches(request):
  """
    This is the main lti launch route. It renders the iframe that shows the via hypothesis app.
    This will fail if hit from any other context.
  """
  return {
    'hypothesis_url': 'https://via.hypothes.is/' + request.params['url']
  }


