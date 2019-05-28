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

Note: The views in this module are currently used only when the new_oauth
feature flag is on. They replace legacy views from ``lti_launches.py``
that're still used when the feature flag is off.
"""
from pyramid.view import view_config, view_defaults
from pyramid.config import not_

from lms.models import ModuleItemConfiguration
from lms.services import CanvasAPIError
from lms.util import via_url
from lms.views.decorators import (
    upsert_h_user,
    upsert_course_group,
    add_user_to_group,
    report_lti_launch,
)


def lti_submit(request, document_url):
    try:
        lis_outcome_service_url = request.params["lis_outcome_service_url"]
        lis_result_sourcedid = request.params["lis_result_sourcedid"]
    except KeyError:
        return
    consumer_key = request.lti_user.oauth_consumer_key

    from lms.models import ApplicationInstance

    secret = (
        request.db.query(ApplicationInstance)
        .filter_by(consumer_key=consumer_key)
        .one()
        .shared_secret
    )

    from requests_oauthlib import OAuth1

    oauth_client = OAuth1(
        client_key=consumer_key,
        client_secret=secret,
        signature_method="HMAC-SHA1",
        signature_type="auth_header",
        force_include_body=True,
    )

    import requests
    from urllib.parse import urlencode

    lti_launch_url = (
        f"http://localhost:8001/lti_launches?speedgrader=true&amp;url={document_url}&amp;grading_user={request.context.h_display_name}"
    )
    response = requests.post(
        url=lis_outcome_service_url,
        data=f"""<?xml version = "1.0" encoding = "UTF-8"?>
<imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
  <imsx_POXHeader>
    <imsx_POXRequestHeaderInfo>
      <imsx_version>V1.0</imsx_version>
      <imsx_messageIdentifier>999999123</imsx_messageIdentifier>
    </imsx_POXRequestHeaderInfo>
  </imsx_POXHeader>
  <imsx_POXBody>
    <replaceResultRequest>
      <resultRecord>
        <sourcedGUID>
          <sourcedId>{ lis_result_sourcedid }</sourcedId>
        </sourcedGUID>
        <result>
          <resultData>
            <ltiLaunchUrl>{ lti_launch_url }</ltiLaunchUrl>
          </resultData>
        </result>
      </resultRecord>
    </replaceResultRequest>
  </imsx_POXBody>
</imsx_POXEnvelopeRequest>""",
        headers={"Content-Type": "application/xml"},
        auth=oauth_client,
    )


@view_defaults(
    decorator=[
        # Before any LTI assignment launch create or update the Hypothesis user
        # and group corresponding to the LTI user and course.
        upsert_h_user,
        upsert_course_group,
        add_user_to_group,
        # Report all LTI assignment launches to the /reports page.
        report_lti_launch,
    ],
    feature_flag="new_oauth",
    permission="launch_lti_assignment",
    renderer="lms:templates/basic_lti_launch/basic_lti_launch.html.jinja2",
    request_method="POST",
    route_name="lti_launches",
)
class BasicLTILaunchViews:
    def __init__(self, request):
        self.request = request

    @view_config(
        canvas_file=True,
        renderer="lms:templates/basic_lti_launch/canvas_file_basic_lti_launch.html.jinja2",
    )
    def canvas_file_basic_lti_launch(self):
        """
        Respond to a Canvas file assignment launch.

        Canvas file assignment launch requests have a ``file_id`` request
        parameter, which is the Canvas instance's ID for the file. To display
        the assignment we have to use this ``file_id`` to get a download URL
        for the file from the Canvas API. We then pass that download URL to
        Via. We have to re-do this file-ID-for-download-URL exchange on every
        single launch because Canvas's download URLs are temporary.
        """
        canvas_api_client = self.request.find_service(name="canvas_api_client")
        file_id = self.request.params["file_id"]

        try:
            document_url = canvas_api_client.public_url(file_id)
        except CanvasAPIError:
            return {}

        return {"via_url": via_url(self.request, document_url)}

    @view_config(db_configured=True)
    def db_configured_basic_lti_launch(self):
        """
        Respond to a DB-configured assignment launch.

        DB-configured assignment launch requests don't have any kind of file ID
        or document URL in the request. Instead the document URL is stored in
        our own DB. This happens with LMS's that don't support LTI content item
        selection/deep linking, so they don't support storing the document URL
        in the LMS and passing it back to us in each launch request. Instead we
        retrieve the document URL from the DB and pass it to Via.
        """
        resource_link_id = self.request.params["resource_link_id"]
        tool_consumer_instance_guid = self.request.params["tool_consumer_instance_guid"]

        # The ``db_configured=True`` view predicate ensures that this view
        # won't be called if there isn't a matching ModuleItemConfiguration in
        # the DB. So here we can safely assume that the ModuleItemConfiguration
        # exists.
        document_url = (
            self.request.db.query(ModuleItemConfiguration)
            .filter_by(
                resource_link_id=resource_link_id,
                tool_consumer_instance_guid=tool_consumer_instance_guid,
            )
            .one()
            .document_url
        )

        return {"via_url": via_url(self.request, document_url)}

    @view_config(url_configured=True, request_param=not_("speedgrader"))
    def url_configured_basic_lti_launch(self):
        """
        Respond to a URL-configured assignment launch.

        URL-configured assignment launch requests have the document URL in the
        ``url`` request parameter. This happens in LMS's that support LTI
        content item selection/deep linking: the document URL is chosen during
        content item selection (during assignment creation) and saved in the
        LMS, which passes it back to us in each launch request. All we have to
        do is pass the URL to Via.
        """
        lti_submit(self.request, self.request.params["url"])
        return {"via_url": via_url(self.request, self.request.params["url"])}

    @view_config(
        authorized_to_configure_assignments=True,
        configured=False,
        decorator=[],  # Disable the class's default decorators just for this view.
        renderer="lms:templates/basic_lti_launch/unconfigured_basic_lti_launch.html.jinja2",
        request_param=not_("speedgrader"),
    )
    def unconfigured_basic_lti_launch(self):
        """
        Respond to an unconfigured assignment launch.

        Unconfigured assignment launch requests don't contain any document URL
        or file ID because the assignment's document hasn't been chosen yet.
        This happens in LMS's that don't support LTI content item
        selection/deep linking. They go straight from assignment creation to
        launching the assignment without the user having had a chance to choose
        a document.

        When this happens we show the user our document-selection form instead
        of launching the assignment. The user will choose the document and
        we'll save it in our DB. Subsequent launches of the same assignment
        will then be DB-configured launches rather than unconfigured.
        """
        return {
            "resource_link_id": self.request.params["resource_link_id"],
            "tool_consumer_instance_guid": self.request.params[
                "tool_consumer_instance_guid"
            ],
            "oauth_consumer_key": self.request.lti_user.oauth_consumer_key,
            "user_id": self.request.lti_user.user_id,
            "context_id": self.request.params["context_id"],
        }

    # pylint:disable=no-self-use
    @view_config(
        authorized_to_configure_assignments=False,
        configured=False,
        decorator=[],  # Disable the class's default decorators just for this view.
        renderer="lms:templates/basic_lti_launch/unconfigured_basic_lti_launch_not_authorized.html.jinja2",
    )
    def unconfigured_basic_lti_launch_not_authorized(self):
        """
        Respond to an unauthorized unconfigured assignment launch.

        This happens when an assignment's document hasn't been chosen yet and
        the assignment is launched by a user who isn't authorized to choose the
        document (for example a learner rather than a teacher). We just show an
        error page.
        """
        return {}

    @view_config(
        decorator=[],  # Disable the default decorators just for this view.
        route_name="module_item_configurations",
    )
    def configure_module_item(self):
        """
        Respond to a configure module item request.

        This happens after an unconfigured assignment launch. We show the user
        our document selection form instead of launching the assignment, and
        when the user chooses a document and submits the form this is the view
        that receives that form submission.

        We save the chosen document in the DB so that subsequent launches of
        this same assignment will be DB-configured rather than unconfigured.
        And we also send back the assignment launch page, passing the chosen
        URL to Via, as the direct response to the content item form submission.
        """
        document_url = self.request.params["document_url"]

        self.request.db.add(
            ModuleItemConfiguration(
                document_url=document_url,
                resource_link_id=self.request.params["resource_link_id"],
                tool_consumer_instance_guid=self.request.params[
                    "tool_consumer_instance_guid"
                ],
            )
        )

        return {"via_url": via_url(self.request, document_url)}

    @view_config(
        decorator=[],  # Disable the default decorators just for this view.
        request_param="speedgrader",
    )
    def speedgrader(self):
        return {"via_url": via_url(self.request, self.request.params["url"])}
