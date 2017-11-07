from pyramid.view import view_config
from lti.util.lti_launch import lti_launch
from lti.util.view_renderer import view_renderer
from lti.models.module_item_configuration import ModuleItemConfiguration

@view_config(route_name='lti_launches',  request_method='POST')
@lti_launch
def lti_launches(request):
  """
    This is the primary lti launch route. There are 3 views that could be rendered:
      1. If a student launches before a teacher has configured the document then it will
         display a message say that the teacher still needs to configure the document.

      2. If a student or teach launch after the document has been configured then it diplays the
         document with the annotation tools.

      3. If a teacher launches and no document has been configured, it renders a form that allows
         them to configure the document.
  """
  if 'url' not in request.params:
    config = request.db.query(ModuleItemConfiguration).filter(
      ModuleItemConfiguration.resource_link_id == request.params['resource_link_id'] and
      ModuleItemConfiguration.tool_consumer_instance_guid == request.params['tool_consumer_instance_guid']
    )
    if config.count() == 1:
      return _view_document(request=request, document_url=config.one().document_url)
    return _new_module_item_configuration(request)

  return _view_document(request=request, document_url=request.params['url'])

@view_renderer(renderer='lti:templates/module_item_configurations/new_module_item_configuration.html.jinja2')
def _new_module_item_configuration(request):
  return {
    'launch_presentation_return_url': request.route_url('module_item_configurations'),
    'form_fields': {
      'resource_link_id': request.params['resource_link_id'],
      'tool_consumer_instance_guid': request.params['tool_consumer_instance_guid']
    }
  }

@view_renderer(renderer='lti:templates/lti_launches/new_lti_launch.html.jinja2')
def _view_document(request, document_url):
  return {
    'hypothesis_url': 'https://via.hypothes.is/' + document_url
  }

