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
from pyramid.view import view_config

from lms.views import helpers


@view_config(
    authorized_to_configure_assignments=True,
    permission="launch_lti_assignment",
    renderer="lms:templates/file_picker.html.jinja2",
    request_method="POST",
    route_name="content_item_selection",
)
def content_item_selection(context, request):
    context.js_config.update(
        {
            # The URL that the JavaScript code will open if it needs the user to
            # authorize us to request a new access token.
            "authUrl": request.route_url("canvas_api.authorize"),
            # The URL that we'll POST the ContentItemSelection form submission
            # (containing the user's selected document) to.
            "formAction": request.params["content_item_return_url"],
            # The fields of the form that we'll POST to the content_item_return_url.
            # (The JavaScript also adds the content item selection itself to the
            # form as another field, in addition to the ones here.)
            "formFields": {
                "lti_message_type": "ContentItemSelection",
                "lti_version": request.params["lti_version"],
            },
            # Variables needed for initializing Google Picker.
            "googleClientId": request.registry.settings["google_client_id"],
            "googleDeveloperKey": request.registry.settings["google_developer_key"],
            # Shown on the "Select PDF from Canvas" button label.
            "lmsName": "Canvas",
            # The "content item selection" that we submit to the
            # content_item_return_url is actually an LTI launch URL with the
            # selected document URL or file_id as a query parameter. To construct
            # these launch URLs our JavaScript code needs the base URL of our LTI
            # launch endpoint.
            "ltiLaunchUrl": request.route_url("lti_launches"),
            # Pass the URL of the LMS that is launching us to our JavaScript code.
            # When we're being launched in an iframe within the LMS our JavaScript
            # needs to pass this URL (which is the URL of the top-most page) to Google
            # Picker, otherwise Picker refuses to launch inside an iframe.
            "customCanvasApiDomain": context.custom_canvas_api_domain,
            "lmsUrl": context.lms_url,
        }
    )

    # For Canvas Picker support our JavaScript needs the ID of the Canvas
    # course, as this is a required param of the API it'll call to get the list
    # of files in the course.
    if helpers.canvas_files_available(request):
        context.js_config["enableLmsFilePicker"] = True
        context.js_config["courseId"] = request.params["custom_canvas_course_id"]
    else:
        context.js_config["enableLmsFilePicker"] = False

    return {}
