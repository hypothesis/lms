
from pyramid.view import view_config
from pyramid.response import Response

from pyramid.renderers import render
from lti.models import application_instance as ai

@view_config(route_name='welcome', request_method='POST')
def create_application_instance(request):
  # TODO handle missing scheme in lms_url
  # check to see if an application instance already exists for this canvas domain
  query = request.db.query(ai.ApplicationInstance).filter(
    ai.ApplicationInstance.lms_url == request.params['lms_url'])

  if query.count() > 0:
    instance = query.one()
  else:
    instance = ai.build_from_lms_url(request.params['lms_url'])
    request.db.add(instance)

  html = render(
    'lti:templates/welcome/create_application_instance.html.jinja2',
    {
      'consumer_key': instance.consumer_key,
      'shared_secret': instance.shared_secret
    }
  )
  return Response(html.encode('utf-8'), content_type='text/html')

@view_config(route_name='welcome')
def welcome(request):
  html = render(
    'lti:templates/welcome/welcome.html.jinja2',
    {}
  )
  return Response(html.encode('utf-8'), content_type='text/html')
