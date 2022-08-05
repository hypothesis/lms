from marshmallow import fields
from marshmallow.validate import Equal
from pyramid.exceptions import HTTPForbidden
from pyramid.view import view_config

from lms.models import ReusedConsumerKey
from lms.security import Permissions
from lms.validation import LTIV11CoreSchema


class GatewayLTISchema(LTIV11CoreSchema):
    location = "form"

    # Specify the context (either assignment or whole course level)
    context_id = fields.Str(required=True)
    context_title = fields.Str(required=True)
    resource_link_id = fields.Str()

    # We don't need these exactly, but it proves the caller is sending us a
    # well-formed LTI request. It also limits us to 1.1, because this whole
    # approach doesn't really work with 1.3 at the moment.
    lti_version = fields.Str(validate=Equal("LTI-1p0"), required=True)
    lti_message_type = fields.Str(
        validate=Equal("basic-lti-launch-request"),
        required=True,
    )


@view_config(
    request_method="POST",
    permission=Permissions.API,
    renderer="json",
    route_name="api.gateway.h.lti",
    schema=GatewayLTISchema,
)
def h_lti(context, request):
    """
    Provide tokens and information to allow customers to query H.

    We expect the user to authenticate with us using an LTI launch.
    """

    # Ensure no funny business is going on trying to access content out of the
    # current application instance scope.
    try:
        context.application_instance.check_guid_aligns(
            request.lti_params["tool_consumer_instance_guid"]
        )
    except ReusedConsumerKey as err:
        raise HTTPForbidden(
            "Claimed `tool_consumer_instance_guid` does not match credentials."
        ) from err

    # Before the credentials we provide will be accepted by `h` the user must
    # exist. So we'll sync over the details to `h`. We also put the user in the
    # course group. This means they will see annotations at the course level
    # right away. If the course uses groups or sections, they won't see
    # anything until they launch an assignment and get put in a group.
    request.find_service(name="lti_h").sync([context.course], request.lti_params)

    return {
        "api": {"h": _GatewayService.render_h_connection_info(request)},
        "data": _GatewayService.render_lti_context(request, context.course),
    }


class _GatewayService:
    @classmethod
    def render_h_connection_info(cls, request):
        h_api_url = request.registry.settings["h_api_url_public"]

        return {
            # These sections are arranged so you can use
            # `requests.Request.request(**data)` and make the correct request
            "list_endpoints": {
                # List the API end-points
                "method": "GET",
                "url": h_api_url,
                "headers": {"Accept": "application/vnd.hypothesis.v2+json"},
            },
            "exchange_grant_token": {
                # Exchange our token for access and refresh tokens
                "method": "POST",
                "url": h_api_url + "token",
                "headers": {
                    "Accept": "application/vnd.hypothesis.v2+json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                "data": {
                    # Generate a short-lived login token for the Hypothesis client
                    "assertion": request.find_service(
                        name="grant_token"
                    ).generate_token(request.lti_user.h_user),
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                },
            },
        }

    @classmethod
    def render_lti_context(cls, request, course):
        h_user = request.lti_user.h_user
        authority = request.registry.settings["h_authority"]
        groupings = request.find_service(name="grouping").get_known_groupings(
            request.user, course
        )

        return {
            # Details of the current user
            "profile": {
                "userid": h_user.userid(authority),
                "display_name": h_user.display_name,
                "lti": {
                    "user_id": h_user.provider_unique_id,
                },
            },
            "groups": [
                {
                    "groupid": grouping.groupid(authority),
                    "name": grouping.lms_name,
                    # In the general case groups can't really have an "LTI"
                    # section because they can come from all over the place.
                    "lms": {
                        "id": grouping.lms_id,
                        "parentId": grouping.parent.lms_id if grouping.parent else None,
                        "type": grouping.type,
                    },
                }
                for grouping in groupings
            ],
        }
