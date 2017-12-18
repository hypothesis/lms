from pyramid.view import view_config
from lms.util.lti_launch import lti_launch
from lms.util.view_renderer import view_renderer
from lms.util.lti_launch import get_application_instance
from lms.models.module_item_configuration import ModuleItemConfiguration
from lms.views.content_item_selection import content_item_form
from lms.util.associate_user import associate_user
from lms.util.canvas_api import CanvasApi, GET
from lms.util.authorize_lms import authorize_lms, save_token
from lms.models.tokens import find_token_by_user_id
from lms.models.application_instance import find_by_oauth_consumer_key


def can_configure_module_item(roles):
    """
    Determine whether or not someone with roles can configure a module item.

    roles should be a list of lti roles
    """
    lower_cased_roles = roles.lower()
    allowed_roles = ['administrator', 'instructor', 'teachingassisstant']
    return any(role in lower_cased_roles for role in allowed_roles)


def is_canvas_file(_request, params):
    """Determine whether we are launching to view a canvas file."""
    return 'canvas_file' in params


def is_url_configured(_request, params):
    """
    Determine whether the requested module item is url configured.

    A module item is url configured when the document url is stored
    in a query paramter on the lti launch url
    """
    return 'url' in params


def is_authorized_to_configure(_request, params):
    """Determine whether the user is allowed to configure module items."""
    return can_configure_module_item(params['roles'])


def is_db_configured(request, params):
    """
    Determine whether or not the requested module item is configured to use db.

    A module item is database configured when it's id and document url are
    stored in our database. This occurs when an lms does not support content
    item selection
    """
    config = request.db.query(ModuleItemConfiguration).filter(
        ModuleItemConfiguration.resource_link_id == params['resource_link_id'] and
        ModuleItemConfiguration.tool_consumer_instance_guid == params[
            'tool_consumer_instance_guid'])
    return config.count() == 1


def handle_lti_launch(request, token=None, lti_params=None, user=None, jwt=None):
    """
    Handle determining which view should be rendered for a given lti launch.

    The following cases are supported:

    1. If a student launches before a teacher has configured the document then it will
    display a message say that the teacher still needs to configure the document.

    2. If a student or teacher launch after the document has been configured then it displays the
    document with the annotation tools.

    3. If a teacher launches and no document has been configured, ict renders a form that allows
    them to configure the document.

    4. If a student or teacher launches a module item that has been configured
       as a canvas file
    """
    if is_url_configured(request, lti_params):
        return _view_document(request, document_url=lti_params['url'], jwt=jwt)

    elif is_db_configured(request, lti_params):
        config = request.db.query(ModuleItemConfiguration).filter(
            ModuleItemConfiguration.resource_link_id == lti_params['resource_link_id'] and
            ModuleItemConfiguration.tool_consumer_instance_guid == lti_params['tool_consumer_instance_guid']
        )
        return _view_document(request, document_url=config.one().document_url, jwt=jwt)
    elif is_canvas_file(request, lti_params):
        token = find_token_by_user_id(request.db, user.id)
        application_instance = find_by_oauth_consumer_key(request.db,
                                                          lti_params['oauth_consumer_key'])
        canvas_api = CanvasApi(token.access_token, application_instance.lms_url)
        file_id = lti_params['file_id']
        result = canvas_api.proxy(f'/api/v1/files/{file_id}/public_url', GET, {})
        if result.ok:
            document_url = result.json()['public_url']
            return _view_document(request, document_url=document_url, jwt=jwt)
        return _unauthorized(request)
    elif is_authorized_to_configure(request, lti_params):
        consumer_key = request.params['oauth_consumer_key']
        application_instance = get_application_instance(request.db, consumer_key)
        return content_item_form(
            request,
            lti_params=request.params,
            content_item_return_url=request.route_url('module_item_configurations'),
            lms_url=application_instance.lms_url,
            jwt=jwt
        )
    return _unauthorized(request)


@view_config(route_name='module_item_launch_oauth_callback',
             request_method='GET')
@save_token
def lti_launch_oauth_callback(request, token, lti_params, user, jwt):
    """Route to handle oauth response from when forced to oauth from lti_launch."""
    return handle_lti_launch(request, token, lti_params, user, jwt)


def should_launch(request):
    """Determine whether or not an oauth should be triggered or not."""
    return is_canvas_file(request, request.params)


@view_config(route_name='lti_launches', request_method='POST')
@lti_launch()
@associate_user
@authorize_lms(
    authorization_base_endpoint='login/oauth2/auth',
    redirect_endpoint='module_item_launch_oauth_callback',
    oauth_condition=should_launch
)
def lti_launches(request, jwt, user=None):
    """Route to handle an lti launch to view a module item."""
    if user is not None:
        token = find_token_by_user_id(request.db, user.id)
        return handle_lti_launch(request, token=token,
                                 lti_params=request.params, user=user, jwt=jwt)
    return _unauthorized(request)


@view_renderer(renderer='lms:templates/lti_launches/new_lti_launch.html.jinja2')
def _view_document(request, document_url, jwt):
    return {
        'hypothesis_url':
        f"{request.registry.settings['via_url']}/{document_url}",
        'jwt': jwt
    }


@view_renderer(renderer='lms:templates/lti_launches/unauthorized.html.jinja2')
def _unauthorized(_):
    return {}
