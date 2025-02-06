"""
Deep Linking related views.

If an LMS (like Canvas) is configured for "deep linking" then we need to send
the results of the file picker to the LMS instead of storing it ourselves. This
is done by the front-end.

When the LMS launches us with a deep linked assignment, we will get the
document url as part of the launch params, instead of reading it from the DB in
`assignment`.
The flow is:

 - LMS calls us on `deep_linking_launch`

    The spec requires that deep linking requests have an ``lti_message_type``
    identifying the launch as a deep linking one but we don't actually rely
    on this parameter: instead we use a separate URL
    to distinguish deep linking launches.

  - We add configuration to enable a callback to the corresponding form_fields view

  - This provides the form data the front end requires to submit to the LMS


For more details see the LTI Deep Linking specs:

 - LTI 1.1 https://www.imsglobal.org/specs/lticiv1p0

   Especially this page:

     https://www.imsglobal.org/specs/lticiv1p0/specification-3

 - LTI 1.3 https://www.imsglobal.org/spec/lti-dl/v2p0

Canvas LMS's Content Item docs are also useful:

  https://canvas.instructure.com/doc/api/file.content_item.html

"""

import json
import uuid
from datetime import datetime, timedelta

from pyramid.view import view_config, view_defaults
from webargs import fields

from lms.events import LTIEvent
from lms.product.plugin.misc import MiscPlugin  # noqa: TC001
from lms.security import Permissions
from lms.services import JWTService, UserService
from lms.validation import DeepLinkingLTILaunchSchema
from lms.validation._base import JSONPyramidRequestSchema
from lms.validation._lti_launch_params import AutoGradingConfigSchema


@view_config(
    permission=Permissions.LTI_CONFIGURE_ASSIGNMENT,
    renderer="lms:templates/file_picker.html.jinja2",
    request_method="POST",
    route_name="content_item_selection",
    schema=DeepLinkingLTILaunchSchema,
)
def deep_linking_launch(context, request):
    """Handle deep linking launches."""

    request.find_service(name="application_instance").update_from_lti_params(
        request.lti_user.application_instance, request.lti_params
    )
    # Keep a record of every LMS user in the DB
    # While request.user gets updated on every request we only need/want to update LMSUser on launches
    request.find_service(UserService).upsert_lms_user(request.user, request.lti_params)

    course = request.find_service(name="course").get_from_launch(
        request.product.family, request.lti_params
    )
    request.find_service(name="lti_h").sync([course], request.params)

    context.js_config.enable_file_picker_mode(
        form_action=request.parsed_params["content_item_return_url"],
        form_fields={
            "lti_message_type": "ContentItemSelection",
            "lti_version": request.parsed_params["lti_version"],
        },
        course=course,
        prompt_for_title=request.product.plugin.misc.deep_linking_prompt_for_title,
    )

    context.js_config.add_deep_linking_api()
    return {}


class DeepLinkingFieldsRequestSchema(JSONPyramidRequestSchema):
    content_item_return_url = fields.Str(required=True)
    content = fields.Dict(required=True)
    group_set = fields.Str(required=False, allow_none=True)
    title = fields.Str(required=False, allow_none=True)

    auto_grading_config = fields.Nested(
        AutoGradingConfigSchema, required=False, allow_none=True
    )


class LTI11DeepLinkingFieldsRequestSchema(DeepLinkingFieldsRequestSchema):
    opaque_data_lti11 = fields.Str(required=False, allow_none=True)


class LTI13DeepLinkingFieldsRequestSchema(DeepLinkingFieldsRequestSchema):
    opaque_data_lti13 = fields.Dict(required=False, allow_none=True)


@view_defaults(request_method="POST", renderer="json")
class DeepLinkingFieldsViews:
    """
    Views that return the required form fields to complete a deep linking request to the LMS.

    After the user picks a document to be annotated the frontend will call these views
    to get all the necessary fields to configure the assignment submitting them in a form to the LMS.
    """

    def __init__(self, request) -> None:
        self.request = request
        self.misc_plugin: MiscPlugin = request.product.plugin.misc

    @view_config(
        route_name="lti.v13.deep_linking.form_fields",
        schema=LTI13DeepLinkingFieldsRequestSchema,
    )
    def file_picker_to_form_fields_v13(self):
        application_instance = self.request.lti_user.application_instance

        assignment_configuration = self._get_assignment_configuration(self.request)

        content_item = {
            "type": "ltiResourceLink",
            # The URL we will be called back on when the
            # assignment is launched from the LMS
            "url": self.misc_plugin.get_deeplinking_launch_url(
                self.request, assignment_configuration
            ),
            # These values should be passed back to us as custom
            # LTI params, but Canvas doesn't seem to.
            "custom": assignment_configuration,
        }
        if title := assignment_configuration.get("title"):
            content_item["title"] = title

        now = datetime.utcnow()  # noqa: DTZ003
        message = {
            "exp": now + timedelta(hours=1),
            "iat": now,
            "iss": application_instance.lti_registration.client_id,
            "sub": application_instance.lti_registration.client_id,
            "aud": application_instance.lti_registration.issuer,
            "nonce": uuid.uuid4().hex,
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": application_instance.deployment_id,
            "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
            "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
            "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [
                content_item
            ],
        }

        # From:
        #  https://www.imsglobal.org/spec/lti-dl/v2p0#deep-linking-response-message
        #
        # The https://purl.imsglobal.org/spec/lti-dl/claim/data value must
        # match the value of the data property of the
        # https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings
        # claim from the `LtiDeepLinkinkingRequest` message.
        #
        # This claim is required if present in the `LtiDeepLinkingRequest`
        # message.
        settings = self.request.parsed_params["opaque_data_lti13"] or {}
        if data := settings.get("data"):
            message["https://purl.imsglobal.org/spec/lti-dl/claim/data"] = data

        self.request.registry.notify(
            LTIEvent.from_request(
                request=self.request,
                type_=LTIEvent.Type.DEEP_LINKING,
                data=assignment_configuration,
            )
        )

        # In LTI1.3 there's just one `JWT` field which includes all the necessary information
        return {
            "JWT": self.request.find_service(JWTService).encode_with_private_key(
                message
            )
        }

    @view_config(
        route_name="lti.v11.deep_linking.form_fields",
        schema=LTI11DeepLinkingFieldsRequestSchema,
    )
    def file_picker_to_form_fields_v11(self):
        """
        Return a JSON-LD `ContentItem` representation of the LTI content.

        See https://www.imsglobal.org/specs/lticiv1p0/specification.
        """
        assignment_configuration = self._get_assignment_configuration(self.request)
        self.request.registry.notify(
            LTIEvent.from_request(
                request=self.request,
                type_=LTIEvent.Type.DEEP_LINKING,
                data=assignment_configuration,
            )
        )

        content_item = {
            "@type": "LtiLinkItem",
            "mediaType": "application/vnd.ims.lti.v1.ltilink",
            # The URL we will be called back on when the
            # assignment is launched from the LMS
            "url": self.misc_plugin.get_deeplinking_launch_url(
                self.request, assignment_configuration
            ),
            # These values should be passed back to us as custom
            # LTI params, but Canvas doesn't seem to.
            "custom": assignment_configuration,
        }

        if title := assignment_configuration.get("title"):
            content_item["title"] = title

        payload = {
            "content_items": json.dumps(
                {
                    "@context": "http://purl.imsglobal.org/ctx/lti/v1/ContentItem",
                    "@graph": [content_item],
                }
            ),
            "lti_message_type": "ContentItemSelection",
            "lti_version": "LTI-1p0",
        }
        if data := self.request.parsed_params.get("opaque_data_lti11"):
            # From: https://www.imsglobal.org/specs/lticiv1p0/specification
            # An opaque value which should be returned by the TP in its response.
            payload["data"] = data

        return self.request.find_service(name="oauth1").sign(
            self.request.lti_user.application_instance,
            self.request.parsed_params["content_item_return_url"],
            "post",
            payload,
        )

    @staticmethod
    def _get_assignment_configuration(request) -> dict:
        """Turn front-end content information into assignment configuration."""
        content = request.parsed_params["content"]

        params = {
            # Always include a UUID in the parameters.
            # This will identify this DL attempt uniquely.
            "deep_linking_uuid": uuid.uuid4().hex,
        }

        if group_set := request.parsed_params.get("group_set"):
            params["group_set"] = group_set

        if title := request.parsed_params.get("title"):
            params["title"] = title

        if auto_grading_config := request.parsed_params.get("auto_grading_config"):
            # Custom params must be str, encode these settings as JSON
            params["auto_grading_config"] = json.dumps(auto_grading_config)

        if content["type"] == "url":
            params["url"] = content["url"]
        else:
            raise ValueError(f"Unknown content type: '{content['type']}'")  # noqa: EM102, TRY003

        return params
