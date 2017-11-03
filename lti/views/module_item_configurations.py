from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from lti.util.lti_launch import lti_launch
import pdb

@view_config(route_name='module_item_configurations', renderer='lti:templates/module_item_configurations/new_module_item_configuration.html.jinja2', request_method='POST')
@lti_launch
def new_module_item_configuration(request):
  # pdb.set_trace()
  # ext_content_return_url
  # launch_presentation_return_url
  return {
    'launch_presentation_return_url': request.params['launch_presentation_return_url'],
    'lti_launch_url': request.route_url('lti_launches') + '?url='
  }


