from pyramid.view import view_config
from lms.util.lti_launch import lti_launch
from lms.util.view_renderer import view_renderer
from lms.util.lti_launch import get_application_instance
from lms.models.module_item_configuration import ModuleItemConfiguration
from lms.views.content_item_selection import content_item_form
from lms.util.associate_user import associate_user
from lms.util.canvas_api import CanvasApi
from lms.util.authorize_lms import authorize_lms, save_token
from lms.models.tokens import find_token_by_user_id
from lms.models.application_instance import find_by_oauth_consumer_key


def can_configure_module_item(roles):
    lower_cased_roles = roles.lower()
    allowed_roles = ['administrator', 'instructor', 'teachingassisstant']
    return any(role in lower_cased_roles for role in allowed_roles)


def is_canvas_file(request, params):
    return 'canvas_file' in params

def is_url_configured(request, params):
    return 'url' in params

def is_authorized_to_configure(request, params):
    return can_configure_module_item(params['roles'])

def is_db_configured(request, params):
    config = request.db.query(ModuleItemConfiguration).filter(
        ModuleItemConfiguration.resource_link_id == params['resource_link_id'] and
        ModuleItemConfiguration.tool_consumer_instance_guid == params['tool_consumer_instance_guid']
        )
    return config.count == 1


# TODO use for non-oauth response route
def handle_lti_launch(request, token=None, lti_params=None, user=None, jwt=None):
    if is_url_configured(request, lti_params): # We are launching from the provided url
        return _view_document(request, document_url=lti_params['url'], jwt=jwt)
    elif is_db_configured(request, lti_params): # We are launching a module item saved in the db
        config = request.db.query(ModuleItemConfiguration).filter(
            ModuleItemConfiguration.resource_link_id == lti_params['resource_link_id'] and
            ModuleItemConfiguration.tool_consumer_instance_guid == lti_params['tool_consumer_instance_guid']
        )
        return _view_document(request, document_url=config.one().document_url, jwt=jwt)
    elif is_canvas_file(request, lti_params): # We are launching a canvas file
        pass
        # TODO Force Oauth
        # TODO Get a public viewing url

        token = find_token_by_user_id(request.db, user.id)
        canvas_domain = find_by_oauth_consumer_key(request.db,
                                                  request.params['oauth_consumer_key'])
        canvas_api = CanvasApi(token, canvas_domain)
        import pdb; pdb.set_trace()
    elif is_authorized_to_configure(request):
        consumer_key = request.params['oauth_consumer_key']
        application_instance = get_application_instance(request.db, consumer_key)
        return content_item_form(
            request,
            lti_params=request.params,
            content_item_return_url=request.route_url('module_item_configurations'),
            lms_url=application_instance.lms_url,
            jwt=jwt
        )
    else: # Not configured
        return _unauthorized(request)


@view_config(route_name='module_item_launch_oauth_callback',
            request_method='GET')
@save_token
def module_item_launch_oauth_callback(request, token, lti_params, user, jwt):
    return handle_lti_launch(request, token, lti_params, user, jwt)



@view_config(route_name='lti_launches', request_method='POST')
@lti_launch()
@associate_user
@authorize_lms(
    authorization_base_endpoint='login/oauth2/auth',
    redirect_endpoint='module_item_launch_oauth_callback'
)
def lti_launches(request, jwt, user=None):
    """
    Primary lms launch route. There are 3 views that could be rendered.

    1. If a student launches before a teacher has configured the document then it will
    display a message say that the teacher still needs to configure the document.

    2. If a student or teacher launch after the document has been configured then it displays the
    document with the annotation tools.

    3. If a teacher launches and no document has been configured, ict renders a form that allows
    them to configure the document.
    """

    if is_url_configured(request): # We are launching from the provided url
        return _view_document(request, document_url=request.params['url'], jwt=jwt)
    elif is_db_configured(request): # We are launching a module item saved in the db
        config = request.db.query(ModuleItemConfiguration).filter(
            ModuleItemConfiguration.resource_link_id == request.params['resource_link_id'] and
            ModuleItemConfiguration.tool_consumer_instance_guid == request.params['tool_consumer_instance_guid']
        )
        return _view_document(request, document_url=config.one().document_url, jwt=jwt)
    elif is_canvas_file(request): # We are launching a canvas file
        pass
        # TODO Force Oauth
        # TODO Get a public viewing url

        token = find_token_by_user_id(request.db, user.id)
        canvas_domain = find_by_oauth_consumer_key(request.db,
                                                  request.params['oauth_consumer_key'])
        canvas_api = CanvasApi(token, canvas_domain)
        import pdb; pdb.set_trace()
    elif is_authorized_to_configure(request):
        consumer_key = request.params['oauth_consumer_key']
        application_instance = get_application_instance(request.db, consumer_key)
        return content_item_form(
            request,
            lti_params=request.params,
            content_item_return_url=request.route_url('module_item_configurations'),
            lms_url=application_instance.lms_url,
            jwt=jwt
        )
    else: # Not configured
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
