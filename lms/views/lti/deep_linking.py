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
from urllib.parse import urlencode, urlparse

from pyramid.view import view_config, view_defaults
from webargs import fields

from lms.security import Permissions
from lms.services import LTIAHTTPService
from lms.validation import DeepLinkingLTILaunchSchema
from lms.validation._base import JSONPyramidRequestSchema


@view_config(
    permission=Permissions.LTI_CONFIGURE_ASSIGNMENT,
    renderer="lms:templates/file_picker.html.jinja2",
    request_method="POST",
    route_name="content_item_selection",
    schema=DeepLinkingLTILaunchSchema,
)
def deep_linking_launch(context, request):
    """Handle deep linking launches."""
    application_instance = request.find_service(
        name="application_instance"
    ).get_current()
    application_instance.update_lms_data(context.lti_params)

    request.find_service(name="lti_h").sync([context.course], request.params)

    context.js_config.enable_file_picker_mode(
        form_action=request.parsed_params["content_item_return_url"],
        form_fields={
            "lti_message_type": "ContentItemSelection",
            "lti_version": request.parsed_params["lti_version"],
        },
    )

    context.js_config.add_deep_linking_api()
    return {}


class DeepLinkingFieldsRequestSchema(JSONPyramidRequestSchema):
    deep_linking_settings = fields.Dict(required=False, allow_none=True)
    content_item_return_url = fields.Str(required=True)
    content = fields.Dict(required=True)

    extra_params = fields.Dict(required=False)


@view_defaults(
    request_method="POST", renderer="json", schema=DeepLinkingFieldsRequestSchema
)
class DeepLinkingFieldsViews:
    """
    Views that return the required form fields to complete a deep linking request to the LMS.

    After the user picks a document to be annotated the frontend will call these views
    to get all the necessary fields to configure the assignment submitting them in a form to the LMS.
    """

    def __init__(self, request):
        self.request = request

    @view_config(route_name="lti.v13.deep_linking.form_fields")
    def file_picker_to_form_fields_v13(self):
        application_instance = self.request.find_service(
            name="application_instance"
        ).get_current()

        message = {
            "https://purl.imsglobal.org/spec/lti/claim/deployment_id": application_instance.deployment_id,
            "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
            "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
            "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [
                {"type": "ltiResourceLink", "url": self._get_content_url(self.request)}
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
        if data := self.request.parsed_params["deep_linking_settings"].get("data"):
            message["https://purl.imsglobal.org/spec/lti-dl/claim/data"] = data

        # In LTI1.3 there's just one `JWT` field which includes all the necessary information
        return {"JWT": self.request.find_service(LTIAHTTPService).sign(message)}

    @view_config(route_name="lti.v11.deep_linking.form_fields")
    def file_picker_to_form_fields_v11(self):
        """
        Return a JSON-LD `ContentItem` representation of the LTI content.

        See https://www.imsglobal.org/specs/lticiv1p0/specification.
        """
        url = self._get_content_url(self.request)

        return {
            "content_items": json.dumps(
                {
                    "@context": "http://purl.imsglobal.org/ctx/lti/v1/ContentItem",
                    "@graph": [
                        {
                            "@type": "LtiLinkItem",
                            "mediaType": "application/vnd.ims.lti.v1.ltilink",
                            "url": url,
                        },
                    ],
                }
            )
        }

    @staticmethod
    def _get_content_url(request):
        """
        Translate content information from the frontend to a launch URL.

        We submit the content information to the LMS as an URL pointing to our
        `lti_launches` endpoint with any information required to identity
        the content as query parameters.
        """
        content = request.parsed_params["content"]

        # Filter out any `null` values to avoid adding a ?key=None on the resulting URL
        params = {
            key: value
            for key, value in (request.parsed_params.get("extra_params") or {}).items()
            if value is not None
        }

        if content["type"] == "file":
            params["canvas_file"] = "true"
            params["file_id"] = content["file"]["id"]
        elif content["type"] == "url":
            params["url"] = content["url"]
        else:
            raise ValueError(f"Unknown content type: '{content['type']}'")

        return (
            urlparse(request.route_url("lti_launches"))
            ._replace(query=urlencode(params))
            .geturl()
        )
