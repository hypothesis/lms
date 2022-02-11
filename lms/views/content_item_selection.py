"""
Views for handling content item selection launches.

A content item selection request is an LTI launch request (so it's a form
submission containing all the usual launch params, including the OAuth 1
signature) that's used by LMS's during the assignment creation process.

When an instructor creates a Hypothesis assignment in an LMS that supports
content item selection the LMS launches our app in order for us to present an
interface for the user to select a "content item" (in our case: a document to
be annotated) for use with the assignment.

The spec requires that content item selection requests have an
``lti_message_type`` parameter with the value ``ContentItemSelectionRequest``,
but we don't actually require the requests to have this parameter: instead we
use a separate URL to distinguish content item selection launches.

When the user selects a document we get the browser to POST the selection back
to the LMS in a form submission with the ``lti_message_type`` parameter set to
``ContentItemSelection``. The original ``ContentItemSelectionRequest``
launch's ``content_item_return_url`` parameter gives us the URL to POST this
form submission to. The LMS saves the selection and passes it back to us in the
launch params whenever this assignment is launched in future.

For more details see the LTI Deep Linking spec:

https://www.imsglobal.org/specs/lticiv1p0

Especially this page:

https://www.imsglobal.org/specs/lticiv1p0/specification-3

Canvas LMS's Content Item docs are also useful:

https://canvas.instructure.com/doc/api/file.content_item.html
"""
import time
import uuid
from urllib.parse import urlencode

from pyramid.view import view_config

from lms.security import Permissions
from lms.validation import ContentItemSelectionLTILaunchSchema
from lms.views.openid import pem_private_key, private_key


@view_config(
    authorized_to_configure_assignments=True,
    permission=Permissions.LTI_LAUNCH_ASSIGNMENT,
    renderer="lms:templates/file_picker.html.jinja2",
    request_method="POST",
    route_name="content_item_selection",
    schema=ContentItemSelectionLTILaunchSchema,
)
def content_item_selection(context, request):
    request.find_service(name="application_instance").get_current().update_lms_data(
        request.params
    )
    lti_launch_url = request.route_url("lti_launches")

    context.get_or_create_course()

    request.find_service(name="lti_h").sync([context.h_group], request.params)
    now = int(time.time())

    request_aud = request.jwt_params["aud"]
    deployment_id = request.jwt_params[
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id"
    ]

    settings = request.jwt_params[
        "https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"
    ]

    document_params = {"url": "https://elpais.com"}

    message = {
        "aud": request.jwt_params["iss"],
        "exp": now + 60 * 60,
        "iat": now,
        "nonce": uuid.uuid4().hex,
        "iss": request_aud,  # client_id?
        "https://purl.imsglobal.org/spec/lti/claim/deployment_id": deployment_id,
        "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
        "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
        "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [
            {
                "type": "ltiResourceLink",
                "title": "A title",
                "text": "This is a link to an activity that will be graded",
                "url": f"{lti_launch_url}?{urlencode(document_params)}",
            }
        ],
        "https://purl.imsglobal.org/spec/lti-dl/claim/data": settings,
    }
    import jwt

    headers = {"kid": private_key["kid"]}

    encoded_message = jwt.encode(
        message, pem_private_key, algorithm="RS256", headers=headers
    )

    context.js_config.enable_content_item_selection_mode(
        form_action=request.parsed_params["content_item_return_url"],
        form_fields={
            "JWT": encoded_message,
        },
        #    "lti_message_type": request.parsed_params["lti_message_type"],
        #    "lti_version": request.parsed_params["lti_version"],
        # },
    )

    return {}
