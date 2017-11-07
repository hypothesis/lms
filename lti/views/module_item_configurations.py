from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from lti.util.lti_launch import lti_launch
from lti.models.module_item_configuration import ModuleItemConfiguration

@view_config(route_name='module_item_configurations', renderer='lti:templates/lti_launches/create_lti_launch.html.jinja2', request_method='POST')
def create_module_item_configuration(request):
  # TODO Verify the user is actually logged in!
  instance = ModuleItemConfiguration(
    document_url=request.params['document_url'],
    resource_link_id=request.params['resource_link_id'],
    tool_consumer_instance_guid=request.params['tool_consumer_instance_guid']
  )
  request.db.add(instance)
  return {
    'hypothesis_url': 'https://via.hypothes.is/' + instance.document_url
  }