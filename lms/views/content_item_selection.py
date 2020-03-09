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


@view_config(
    authorized_to_configure_assignments=True,
    permission="launch_lti_assignment",
    renderer="lms:templates/file_picker.html.jinja2",
    request_method="POST",
    route_name="content_item_selection",
)
def content_item_selection(context, request):
    lti_h_service = request.find_service(name="lti_h")
    lti_h_service.upsert_h_user()
    lti_h_service.upsert_course_group()

    context.js_config.enable_content_item_selection_mode(
        form_action=request.params["content_item_return_url"],
        form_fields={
            "lti_message_type": "ContentItemSelection",
            "lti_version": request.params["lti_version"],
        },
    )

    return {}
