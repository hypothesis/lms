from __future__ import unicode_literals

from pyramid.view import view_config

from lms.exceptions import MissingLTIContentItemParamError
from lms.util import lti_launch
from lms.util.view_renderer import view_renderer
from lms.util.associate_user import associate_user
from lms.util.authorize_lms import authorize_lms
from lms.views.decorators import legacy_upsert_h_user
from lms.views.decorators import legacy_create_course_group
from lms.views.helpers import canvas_files_available


@view_config(route_name="content_item_selection", request_method="POST")
@lti_launch
@legacy_upsert_h_user
@legacy_create_course_group
@associate_user
@authorize_lms(
    authorization_base_endpoint="login/oauth2/auth",
    redirect_endpoint="canvas_oauth_callback",
    oauth_condition=canvas_files_available,
)
def content_item_selection(request, _jwt, **_):
    """
    Render the form that teachers see to configure the module item.

    This view is only used for lms's that support link selection
    """
    lms_url = request.find_service(name="ai_getter").lms_url(
        request.params["oauth_consumer_key"]
    )
    return content_item_form(
        request,
        lti_params=request.params,
        lms_url=lms_url,
        content_item_return_url=request.params["content_item_return_url"],
        jwt=None,
    )


@view_renderer(
    renderer="lms:templates/content_item_selection/new_content_item_selection.html.jinja2"
)
def content_item_form(request, lti_params, lms_url, content_item_return_url, jwt=None):
    for param in ["lti_version", "oauth_version", "oauth_nonce", "oauth_signature"]:
        if param not in lti_params:
            raise MissingLTIContentItemParamError(param)

    form_fields = {
        "context_id": lti_params["context_id"],
        "user_id": lti_params["user_id"],
        "lti_message_type": "ContentItemSelection",
        "lti_version": lti_params["lti_version"],
        "oauth_version": lti_params["oauth_version"],
        "oauth_nonce": lti_params["oauth_nonce"],
        "oauth_consumer_key": lti_params["oauth_consumer_key"],
        "oauth_signature_method": lti_params["oauth_signature_method"],
        "oauth_signature": lti_params["oauth_signature"],
        "jwt_token": jwt,
    }
    # These fields appear in blackboard launches, but not in canvas
    # launches
    if "resource_link_id" in lti_params:
        form_fields["resource_link_id"] = lti_params["resource_link_id"]
    if "tool_consumer_instance_guid" in lti_params:
        form_fields["tool_consumer_instance_guid"] = lti_params[
            "tool_consumer_instance_guid"
        ]

    custom_lms_url = None
    if "custom_canvas_api_domain" in lti_params:
        custom_lms_url = lti_params["custom_canvas_api_domain"]

    params = {
        "content_item_return_url": content_item_return_url,
        "lti_launch_url": request.route_url("lti_launches"),
        "form_fields": form_fields,
        "google_client_id": request.registry.settings["google_client_id"],
        "google_developer_key": request.registry.settings["google_developer_key"],
        "google_app_id": request.registry.settings["google_app_id"],
        "lms_url": lms_url if custom_lms_url is None else custom_lms_url,
        "api_url": request.route_url("canvas_proxy"),
        "jwt": jwt,
    }

    if canvas_files_available(request, params=lti_params):
        params["course_id"] = lti_params["custom_canvas_course_id"]
    return params
