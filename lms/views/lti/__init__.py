"""
Views for handling what the LTI spec calls "Basic LTI Launches".

A Basic LTI Launch is the form submission POST request that an LMS sends us
when it wants our app to launch an assignment, as opposed to other kinds of
LTI launches such as the Content Item Selection launches that some LMS's
send us while *creating* a new assignment.

The spec requires Basic LTI Launch requests to have an ``lti_message_type``
parameter with the value ``basic-lti-launch-request`` to distinguish them
from other types of launch request (other "message types") but our code
doesn't actually require basic launch requests to have this parameter.
"""

from pyramid.view import view_config

from lms.services import HAPIError
from lms.views.helpers import via_url


@view_config(
    permission="launch_lti_assignment",
    renderer="lms:templates/basic_lti_launch/basic_lti_launch.html.jinja2",
    request_method="POST",
)
class LTIViewBaseClass:
    def __init__(self, context, request):
        self.context = context
        self.request = request

        # Configure the front-end mini-app to run.
        self.context.js_config.update({"mode": "basic-lti-launch"})

        # Add config used by frontend to call `record_submission` API.
        params = self.request.params
        if (
            # The outcome reporting params are typically only available when
            # students (not teachers) launch an assignment.
            params.get("lis_result_sourcedid")
            and params.get("lis_outcome_service_url")
            # This feature is initially restricted to Canvas.
            and params.get("tool_consumer_info_product_family_code") == "canvas"
        ):
            self.context.js_config["submissionParams"] = {}

            self._set_submission_param("h_username", context.h_user.username)
            self._set_submission_param(
                "lis_result_sourcedid", params.get("lis_result_sourcedid")
            )
            self._set_submission_param(
                "lis_outcome_service_url", params.get("lis_outcome_service_url")
            )

        # If the launch has been configured to focus on the annotations from
        # a particular user, translate that into Hypothesis client configuration.
        focused_user = self.request.params.get("focused_user")
        if focused_user:
            self._set_focused_user(focused_user)

    def _set_submission_param(self, name, value):
        """Update config for frontend's calls to `report_submisssion` API."""

        if "submissionParams" in self.context.js_config:
            self.context.js_config["submissionParams"][name] = value

    def _set_focused_user(self, username):
        """Configure the Hypothesis client to focus on a particular user."""

        h_api_client = self.request.find_service(name="h_api_client")

        try:
            display_name = h_api_client.get_user(username).display_name
        except HAPIError:
            # If we couldn't fetch the student's name for any reason, fall back
            # to a placeholder rather than giving up entirely, since the rest
            # of the experience can still work.
            display_name = "(Couldn't fetch student name)"

        self.context.hypothesis_config.update(
            {"focus": {"user": {"username": username, "displayName": display_name}}}
        )

    def _set_via_url(self, document_url):
        """Configure content URL which the frontend will render inside an iframe."""
        self.context.js_config["urls"].update(
            {"via_url": via_url(self.request, document_url)}
        )
        self._set_submission_param("document_url", document_url)
