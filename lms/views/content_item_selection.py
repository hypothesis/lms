from pyramid.view import view_config
from lms.config import env_setting
from lms.util.lti_launch import get_application_instance
from lms.util.lti_launch import lti_launch
from lms.util.view_renderer import view_renderer
from lms.util.associate_user import associate_user
from lms.util.authorize_lms import authorize_lms


@view_config(route_name='content_item_selection', request_method='POST')
@lti_launch()
@associate_user
@authorize_lms(
    authorization_base_endpoint='login/oauth2/auth',
    redirect_endpoint='canvas_oauth_callback'
)
def content_item_selection(request, _, _user=None):
    """
    Render the form that teachers see to configure the module item.

    This view is only used for lms's that support link selection
    """
    consumer_key = request.params['oauth_consumer_key']
    application_instance = get_application_instance(request.db, consumer_key)
    return content_item_form(
        request,
        lti_params=request.params,
        lms_url=application_instance.lms_url,
        content_item_return_url=request.params['content_item_return_url'],
        jwt=None
    )


@view_renderer(
    renderer='lms:templates/content_item_selection/new_content_item_selection.html.jinja2')
def content_item_form(request, lti_params, lms_url, content_item_return_url,
        canvas_files=[],jwt=None):
    return {
        'content_item_return_url': content_item_return_url,
        'lti_launch_url': request.route_url('lti_launches'),
        'canvas_files': canvas_files,
        'form_fields': {
            'lti_message_type': 'ContentItemSelection',
            'lti_version': lti_params['lti_version'],
            'oauth_version': lti_params['oauth_version'],
            'oauth_nonce': lti_params['oauth_nonce'],
            'oauth_consumer_key': lti_params['oauth_consumer_key'],
            'oauth_signature_method': lti_params['oauth_signature_method'],
            'oauth_signature': lti_params['oauth_signature'],
            'resource_link_id': lti_params['oauth_signature'],
            'tool_consumer_instance_guid': lti_params['oauth_signature'],
            'jwt_token': jwt
        },
        'google_client_id': env_setting('GOOGLE_CLIENT_ID'),
        'google_developer_key': env_setting('GOOGLE_DEVELOPER_KEY'),
        'google_app_id': env_setting('GOOGLE_APP_ID'),
        'lms_url': lms_url
    }
