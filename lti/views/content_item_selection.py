from pyramid.view import view_config
from lti.util.lti_launch import lti_launch


@view_config(
  route_name='content_item_selection',
  renderer='lti:templates/content_item_selection/new_content_item_selection.html.jinja2',
  request_method='POST')
@lti_launch
def content_item_selection(request):
  """
    Renders the form that teachers see to configure the module item.
    This view is only used for lms's that support link selection
  """
  return {
    'content_item_return_url': request.params['content_item_return_url'],
    'lti_launch_url': request.route_url('lti_launches'),
    'form_fields': {
      'lti_message_type': 'ContentItemSelection',
      'lti_version': request.params['lti_version'],
      'oauth_version': request.params['oauth_version'],
      'oauth_nonce': request.params['oauth_nonce'],
      'oauth_consumer_key': request.params['oauth_consumer_key'],
      'oauth_signature_method': request.params['oauth_signature_method'],
      'oauth_signature': request.params['oauth_signature'],
    }
  }
