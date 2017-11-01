
from pyramid.view import view_config
from pyramid.response import Response

from pyramid.renderers import render
from lti.models import application_instance as ai

@view_config(route_name='application_instance')
def create_application_instance(request):
    instance = ai.build_from_lms_url("")
    request.db.add(instance)
    html = render(
      'lti:templates/application_instance/show_application_instance.html.jinja2', 
       {
         "consumer_key": instance.consumer_key,
         "shared_secret": instance.shared_secret
       }
     )
    return Response(html.encode('utf-8'), content_type='text/html')
