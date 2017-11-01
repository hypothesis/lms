
from pyramid.view import view_config

from pyramid.renderers import render

@view_config(route_name='application_instance')
def create_application_instance(request):
    html = render('lti:templates/html_assignment.html.jinja2', dict(
        name=name,
        url=request.registry.settings['via_url'] + '/' + url,
        oauth_consumer_key=oauth_consumer_key,
        lis_outcome_service_url=lis_outcome_service_url,
        lis_result_sourcedid=lis_result_sourcedid,
        lti_server=request.registry.settings['lti_server'],
        client_origin=request.registry.settings['client_origin'],
    ))
    return Response(html.encode('utf-8'), content_type='text/html')
