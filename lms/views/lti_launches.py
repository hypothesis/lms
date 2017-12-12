import sqlalchemy
import logging
from pyramid.view import view_config

from lms.models import ApplicationInstance
from lms.models.lti_launches import LtiLaunches
from lms.util.lti_launch import lti_launch
from lms.util.view_renderer import view_renderer
from lms.util.lti_launch import get_application_instance
from lms.models.module_item_configuration import ModuleItemConfiguration
from lms.views.content_item_selection import content_item_form


def can_configure_module_item(roles):
    lower_cased_roles = roles.lower()
    allowed_roles = ['administrator', 'instructor', 'teachingassisstant']
    return any(role in lower_cased_roles for role in allowed_roles)


@view_config(route_name='lti_launches', request_method='POST')
@lti_launch
def lti_launches(request, jwt):
    """
    Primary lms launch route. There are 3 views that could be rendered.

    1. If a student launches before a teacher has configured the document then it will
    display a message say that the teacher still needs to configure the document.

    2. If a student or teacher launch after the document has been configured then it displays the
    document with the annotation tools.

    3. If a teacher launches and no document has been configured, ict renders a form that allows
    them to configure the document.
    """
    log = logging.getLogger(__name__)

    if 'url' not in request.params:
        config = request.db.query(ModuleItemConfiguration).filter(
            ModuleItemConfiguration.resource_link_id == request.params[
                'resource_link_id'] and
            ModuleItemConfiguration.tool_consumer_instance_guid ==
            request.params['tool_consumer_instance_guid']
        )
        if config.count() >= 1:
            return _view_document(request,
                                  document_url=config.one().document_url,
                                  jwt=jwt)
        elif can_configure_module_item(request.params['roles']):
            consumer_key = request.params['oauth_consumer_key']
            application_instance = get_application_instance(request.db,
                                                            consumer_key)
            return content_item_form(
                request,
                content_item_return_url=request.route_url(
                    'module_item_configurations'),
                lms_url=application_instance.lms_url,
                jwt=jwt
            )
        return _unauthorized(request)

    try:
        lti_key = request.params['oauth_consumer_key']
        query = request.db.query(ApplicationInstance).filter(
            ApplicationInstance.consumer_key == lti_key)
        application_instance_id = query.one().id
        context_id = request.params['context_id']
        lti_launch_instance = LtiLaunches(
            context_id=context_id,
            application_instance_id=application_instance_id
        )
        request.db.add(lti_launch_instance)

    except Exception as e:
        # Never prevent a launch because of logging problem.
        log.error(f"Failed to log lti launch for lti key '{lti_key}': {e}")

    return _view_document(request, document_url=request.params['url'], jwt=jwt)


@view_renderer(renderer='lms:templates/lti_launches/new_lti_launch.html.jinja2')
def _view_document(_, document_url, jwt):
    return {
        'hypothesis_url': 'https://via.hypothes.is/' + document_url,
        'jwt': jwt
    }


@view_renderer(renderer='lms:templates/lti_launches/unauthorized.html.jinja2')
def _unauthorized(_):
    return {}
