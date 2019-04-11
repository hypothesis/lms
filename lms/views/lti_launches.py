import logging
from datetime import datetime

from pyramid.view import view_config
from sqlalchemy import and_
from lms.exceptions import MissingLTILaunchParamError
from lms.models.lti_launches import LtiLaunches
from lms.models.module_item_configuration import ModuleItemConfiguration
from lms.util import lti_launch
from lms.util.view_renderer import view_renderer
from lms.views.content_item_selection import content_item_form
from lms.util.associate_user import associate_user
from lms.util.canvas_api import CanvasApi, GET
from lms.util.authorize_lms import authorize_lms, save_token
from lms.util import via_url
from lms.models.tokens import find_token_by_user_id
from lms.views.decorators import upsert_h_user
from lms.views.decorators import create_course_group
from lms.views.decorators import add_user_to_group


def can_configure_module_item(roles):
    """
    Determine whether or not someone with roles can configure a module item.

    roles should be a list of lti roles
    """
    lower_cased_roles = roles.lower()
    allowed_roles = ["administrator", "instructor", "teachingassisstant"]
    return any(role in lower_cased_roles for role in allowed_roles)


def is_canvas_file(_request, params):
    """Determine whether we are launching to view a canvas file."""
    return "canvas_file" in params


def is_url_configured(_request, params):
    """
    Determine whether the requested module item is url configured.

    A module item is url configured when the document url is stored
    in a query paramter on the lti launch url
    """
    return "url" in params


def is_authorized_to_configure(_request, params):
    """Determine whether the user is allowed to configure module items."""
    try:
        roles = params["roles"]
    except KeyError:
        raise MissingLTILaunchParamError("roles")
    return can_configure_module_item(roles)


def is_db_configured(request, params):
    """
    Determine whether or not the requested module item is configured to use db.

    A module item is database configured when it's id and document url are
    stored in our database. This occurs when an lms does not support content
    item selection
    """
    try:
        resource_link_id = params["resource_link_id"]
    except KeyError:
        raise MissingLTILaunchParamError("resource_link_id")

    config = request.db.query(ModuleItemConfiguration).filter(
        and_(
            ModuleItemConfiguration.resource_link_id == resource_link_id,
            ModuleItemConfiguration.tool_consumer_instance_guid
            == params["tool_consumer_instance_guid"],
        )
    )
    return config.count() == 1


def launch_lti(request, lti_key=None, context_id=None, document_url=None, jwt=None):
    log = logging.getLogger(__name__)
    try:
        lti_launch_instance = LtiLaunches(
            context_id=context_id, lti_key=lti_key, created=datetime.utcnow()
        )
        request.db.add(lti_launch_instance)

    # Never prevent a launch because of logging problem.
    # pylint: disable=broad-except
    except Exception as e:
        log.error("Failed to log lti launch for lti key '%s': %s", lti_key, e)

    return _view_document(request, document_url=document_url, jwt=jwt)


def _check_params(lti_params):
    """Raise a MissingLTILaunchParamError when a required parameter is missing from an LTI launch request."""
    required_params = [
        "oauth_consumer_key",
        "context_id",
        "tool_consumer_instance_guid",
    ]

    for required_param in required_params:
        try:
            lti_params[required_param]
        except KeyError:
            raise MissingLTILaunchParamError(required_param)


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
    _check_params(lti_params)

    lti_key = lti_params["oauth_consumer_key"]
    context_id = lti_params["context_id"]
    tool_consumer_instance_guid = lti_params["tool_consumer_instance_guid"]

    if is_url_configured(request, lti_params):
        return launch_lti(
            request,
            lti_key=lti_key,
            context_id=context_id,
            document_url=lti_params["url"],
            jwt=jwt,
        )

    if is_db_configured(request, lti_params):
        config = request.db.query(ModuleItemConfiguration).filter(
            and_(
                ModuleItemConfiguration.resource_link_id
                == lti_params["resource_link_id"],
                ModuleItemConfiguration.tool_consumer_instance_guid
                == tool_consumer_instance_guid,
            )
        )
        return launch_lti(
            request,
            lti_key=lti_key,
            context_id=context_id,
            document_url=config.one().document_url,
            jwt=jwt,
        )

    if is_canvas_file(request, lti_params):
        token = find_token_by_user_id(request.db, user.id)
        lms_url = request.find_service(name="ai_getter").lms_url(
            lti_params["oauth_consumer_key"]
        )
        canvas_api = CanvasApi(token.access_token, lms_url)
        file_id = lti_params["file_id"]
        result = canvas_api.proxy(f"/api/v1/files/{file_id}/public_url", GET, {})
        if result.status_code < 400:
            document_url = result.json()["public_url"]
            return launch_lti(
                request,
                lti_key=lti_key,
                context_id=context_id,
                document_url=document_url,
                jwt=jwt,
            )
        return _unauthorized(request)

    if is_authorized_to_configure(request, lti_params):
        consumer_key = request.params["oauth_consumer_key"]
        lms_url = request.find_service(name="ai_getter").lms_url(consumer_key)
        return content_item_form(
            request,
            lti_params=request.params,
            content_item_return_url=request.route_url("module_item_configurations"),
            lms_url=lms_url,
            jwt=jwt,
        )
    return _unauthorized(request)


@view_config(route_name="module_item_launch_oauth_callback", request_method="GET")
@save_token
def lti_launch_oauth_callback(request, token, lti_params, user, jwt):
    """Route to handle oauth response from when forced to oauth from lti_launch."""
    return handle_lti_launch(request, token, lti_params, user, jwt)


def should_launch(request):
    """Determine whether or not an oauth should be triggered or not."""
    return is_canvas_file(request, request.params)


@view_config(route_name="lti_launches", request_method="POST")
@lti_launch
@upsert_h_user
@create_course_group
@add_user_to_group
@associate_user
@authorize_lms(
    authorization_base_endpoint="login/oauth2/auth",
    redirect_endpoint="module_item_launch_oauth_callback",
    oauth_condition=should_launch,
)
def lti_launches(request, jwt, user=None):
    """Route to handle an lti launch to view a module item."""
    if request.feature("new_oauth"):
        from pyramid.renderers import render_to_response

        return render_to_response("lms:templates/test.html.jinja2", {}, request)
    if user is not None:
        token = find_token_by_user_id(request.db, user.id)
        return handle_lti_launch(
            request, token=token, lti_params=request.params, user=user, jwt=jwt
        )
    return _unauthorized(request)


@view_renderer(renderer="lms:templates/lti_launches/new_lti_launch.html.jinja2")
def _view_document(request, document_url, jwt):
    return {"via_url": via_url(request, document_url), "jwt": jwt}


@view_renderer(renderer="lms:templates/lti_launches/unauthorized.html.jinja2")
def _unauthorized(_):
    return {}
