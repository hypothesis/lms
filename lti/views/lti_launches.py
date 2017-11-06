from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from lti.util.lti_launch import lti_launch, view_renderer
from lti.models.module_item_configuration import ModuleItemConfiguration
@view_config(route_name='lti_launches',  request_method='POST')
@lti_launch
def lti_launches(request):
  """
    This is the main lti launch route. It renders the iframe that shows the via hypothesis app.
    This will fail if hit from any other context.
  """
  if 'url' not in request.params:
    config = request.db.query(ModuleItemConfiguration).filter(
      ModuleItemConfiguration.resource_link_id == request.params['resource_link_id'] and
      ModuleItemConfiguration.tool_consumer_instance_guid == request.params['tool_consumer_instance_guid']
    )
    if config.count() == 1:
      return _view_document(request=request, document_url=config.one().document_url)
    return _new_module_item_conifiguration(request)

  return {
    'hypothesis_url': 'https://via.hypothes.is/' + request.params['url']
  }

@view_renderer(renderer='lti:templates/module_item_configurations/new_module_item_configuration.html.jinja2')
def _new_module_item_conifiguration(request):
  return {
    'launch_presentation_return_url': request.route_url('create_module_item_configuration'),
    'form_fields': {
      'resource_link_id': request.params['resource_link_id'],
      'tool_consumer_instance_guid': request.params['tool_consumer_instance_guid']
    }
  }

@view_renderer(renderer='lti:templates/lti_launches/create_lti_launch.html.jinja2')
def _view_document(request, document_url):
  return {
    'hypothesis_url': 'https://via.hypothes.is/' + document_url
  }

