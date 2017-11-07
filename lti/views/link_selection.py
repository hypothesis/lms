from pyramid.view import view_config
from lti.util.lti_launch import lti_launch

@view_config(route_name='link_selection', renderer='lti:templates/module_item_configurations/new_module_item_configuration.html.jinja2', request_method='POST')
@lti_launch
def link_selection(request):
  """
    Renders the form that teachers see to configure the module item.
    This view is only used for lms's that support link selection
  """
  return {
    'launch_presentation_return_url': request.params['launch_presentation_return_url'],
    'form_fields': {
      'url': request.route_url('lti_launches') + '?url='
    }
  }