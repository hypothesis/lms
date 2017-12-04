from pyramid.view import view_config
from lms.config import env_setting
from lms.util.lti_launch import get_application_instance
from lms.util.lti_launch import lti_launch
from lms.util.view_renderer import view_renderer
from lms.util.associate_user import associate_user
from lms.util.authorize_lms import authorize_lms
from lms.models.oauth_state import find_by_state
import json

def look_up_lti_params(request):
    if('oauth_consumer_key' in request.params):
        return request.params
    elif('state' in request.params):
        oauth_state = find_by_state(request.db, request.params['state'])
        return json.loads(oauth_state.lti_params)
    return None

@view_config(route_name='content_item_selection', request_method='POST')
@view_config(route_name='content_item_selection', request_method='GET')
@lti_launch(get_lti_launch_params=look_up_lti_params)
@associate_user
# TODO read from ini file
@authorize_lms(
 client_id = "43460000000000123",
 client_secret = "TSeQ7E3dzbHgu5ydX2xCrKJiXTmfJbOeLogm3sj0ESxCxlsxTSaDAObOK46XEZ84",
 authorization_base_url = 'https://atomicjolt.instructure.com/login/oauth2/auth',
 token_url = 'https://atomicjolt.instructure.com/login/oauth2/token',
 redirect_uri = 'https://8b608e88.ngrok.io/canvas_oauth_callback'
)
def content_item_selection(request, _, user=None):
    """
    Render the form that teachers see to configure the module item.

    This view is only used for lms's that support link selection
    """
    consumer_key = request.params['oauth_consumer_key']
    application_instance = get_application_instance(request.db, consumer_key)
    return content_item_form(
        request,
        lms_url=application_instance.lms_url,
        content_item_return_url=request.params['content_item_return_url'],
        jwt=None
    )


@view_renderer(
    renderer='lms:templates/content_item_selection/new_content_item_selection.html.jinja2')
def content_item_form(request, lms_url, content_item_return_url, jwt=None):
    return {
        'content_item_return_url': content_item_return_url,
        'lti_launch_url': request.route_url('lti_launches'),
        'form_fields': {
            'lti_message_type': 'ContentItemSelection',
            'lti_version': request.params['lti_version'],
            'oauth_version': request.params['oauth_version'],
            'oauth_nonce': request.params['oauth_nonce'],
            'oauth_consumer_key': request.params['oauth_consumer_key'],
            'oauth_signature_method': request.params['oauth_signature_method'],
            'oauth_signature': request.params['oauth_signature'],
            'resource_link_id': request.params['oauth_signature'],
            'tool_consumer_instance_guid': request.params['oauth_signature'],
            'jwt_token': jwt
        },
        'google_client_id': env_setting('GOOGLE_CLIENT_ID'),
        'google_developer_key': env_setting('GOOGLE_DEVELOPER_KEY'),
        'google_app_id': env_setting('GOOGLE_APP_ID'),
        'lms_url': lms_url
    }
