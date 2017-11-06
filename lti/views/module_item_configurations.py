from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from lti.util.lti_launch import lti_launch
from lti.models.module_item_configuration import ModuleItemConfiguration
@view_config(route_name='module_item_configurations', renderer='lti:templates/module_item_configurations/new_module_item_configuration.html.jinja2', request_method='POST')
@lti_launch
def new_module_item_configuration(request):
  """
    Renders the form that teachers see to configure the module item.
  """
  return {
    'launch_presentation_return_url': request.params['launch_presentation_return_url'],
    'form_fields': {
      'url': request.route_url('lti_launches') + '?url='
    }
  }

@view_config(route_name='create_module_item_configuration', renderer='lti:templates/lti_launches/create_lti_launch.html.jinja2', request_method='POST')
def create_module_item_configuration(request):
  instance = ModuleItemConfiguration(
    document_url=request.params['document_url'],
    resource_link_id=request.params['resource_link_id'],
    tool_consumer_instance_guid=request.params['tool_consumer_instance_guid']
  )
  request.db.add(instance)
  return {
    'hypothesis_url': 'https://via.hypothes.is/' + instance.document_url
  }