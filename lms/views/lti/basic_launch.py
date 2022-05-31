"""
Views for handling what the LTI spec calls "Basic LTI Launches".

A Basic LTI Launch is the form submission POST request that an LMS sends us
when it wants our app to launch an assignment, as opposed to other kinds of
LTI launches such as the deep linking launches that some LMS's
send us while *creating* a new assignment.

The spec requires Basic LTI Launch requests to have an ``lti_message_type``
parameter with the value ``basic-lti-launch-request`` to distinguish them
from other types of launch request (other "message types") but our code
doesn't actually require basic launch requests to have this parameter.
"""

from pyramid.view import view_config, view_defaults

from lms.models import LtiLaunches
from lms.resources._js_config import JSConfig
from lms.security import Permissions
from lms.services.vitalsource.client import VitalSourceService
from lms.validation import (
    BasicLTILaunchSchema,
    ConfigureAssignmentSchema,
    URLConfiguredBasicLTILaunchSchema,
)
from lms.validation.authentication import BearerTokenSchema
from lms.views.predicates import BlackboardCopied, BrightspaceCopied


@view_defaults(
    permission=Permissions.LTI_LAUNCH_ASSIGNMENT,
    renderer="lms:templates/lti/basic_launch/basic_launch.html.jinja2",
    request_method="POST",
    route_name="lti_launches",
    schema=BasicLTILaunchSchema,
)
class BasicLaunchViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.assignment_service = request.find_service(name="assignment")

        self.context.js_config.enable_lti_launch_mode()
        self.context.js_config.maybe_set_focused_user()

        self.application_instance = request.find_service(
            name="application_instance"
        ).get_current()
        self.application_instance.update_lms_data(self.context.lti_params)

    def do_launch(self, document_url, grading_supported=True):
        """Do a basic LTI launch with the given document_url."""
        self.sync_lti_data_to_h()
        self.store_lti_data()

        if grading_supported:
            self.context.js_config.maybe_enable_grading()

        self.context.js_config.add_document_url(document_url)

        return {}

    def sync_lti_data_to_h(self):
        """
        Sync LTI data to H.

        Before any LTI assignment launch create or update the Hypothesis user
        and group corresponding to the LTI user and course.
        """

        self.request.find_service(name="lti_h").sync(
            [self.context.get_or_create_course()], self.request.params
        )

    def store_lti_data(self):
        """Store LTI launch data in our LMS database."""

        request = self.request

        # Report all LTI assignment launches to the /reports page.
        LtiLaunches.add(
            request.db,
            request.params.get("context_id"),
            request.params.get("oauth_consumer_key"),
        )

        lti_user = request.lti_user

        if not lti_user.is_instructor and not self.context.is_canvas:
            # Create or update a record of LIS result data for a student launch
            request.find_service(name="grading_info").upsert_from_request(request)

    @view_config(vitalsource_book=True)
    def legacy_vitalsource_launch(self):
        """
        Respond to a legacy configured VitalSource assignment.

        Legacy VitalSource assignments use `vitalsource_book=true` as opposed to
        a `vitalsource://` URL as the document_url.

        The assignment shouldn't be "configured" in any other way to match this view.
        """
        book_id = self.request.params["book_id"]
        cfi = self.request.params.get("cfi")

        document_url = VitalSourceService.generate_document_url(book_id, cfi)

        return self.do_launch(document_url=document_url, grading_supported=True)

    @view_config(canvas_file=True)
    def canvas_file_launch(self):
        """
        Respond to a Canvas file assignment launch which is not db_configured.

        Canvas file assignment launch requests have a ``file_id`` request
        parameter, which is the Canvas instance's ID for the file. To display
        the assignment we have to use this ``file_id`` to get a download URL
        for the file from the Canvas API. We then pass that download URL to
        Via. We have to re-do this file-ID-for-download-URL exchange on every
        single launch because Canvas's download URLs are temporary.
        """
        course_id = self.context.lti_params["custom_canvas_course_id"]
        file_id = self.request.params["file_id"]

        # Normally this would be done during `configure_assignment()` but
        # Canvas skips that step. We are doing this to ensure that there is a
        # module item configuration. As a result of this we can rely on this
        # being around in future code.
        document_url = f"canvas://file/course/{course_id}/file_id/{file_id}"
        self.assignment_service.upsert(
            document_url=document_url,
            tool_consumer_instance_guid=self.context.lti_params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=self.context.resource_link_id,
        )
        return self.do_launch(document_url=document_url, grading_supported=False)

    @view_config(db_configured=True, canvas_file=False, url_configured=False)
    def db_configured_launch(self):
        """
        Respond to a DB-configured assignment launch.

        DB-configured assignment launch requests don't have any kind of file ID
        or document URL in the request. Instead the document URL is stored in
        our own DB. This happens with LMS's that don't support LTI deep linking,
        so they don't support storing the document URL
        in the LMS and passing it back to us in each launch request. Instead we
        retrieve the document URL from the DB and pass it to Via.
        """
        # The ``db_configured=True`` view predicate ensures that this view
        # won't be called if there isn't a matching document_url in the DB. So
        # here we can safely assume that the document_url exists.
        document_url = self.assignment_service.get(
            self.context.lti_params["tool_consumer_instance_guid"],
            self.context.resource_link_id,
        ).document_url
        return self.do_launch(document_url)

    @view_config(blackboard_copied=True)
    def blackboard_copied_launch(self):
        """
        Respond to a launch of a newly-copied Blackboard assignment.

        For more about Blackboard course copy see the BlackboardCopied
        predicate's docstring.
        """
        return self.course_copied_launch(
            BlackboardCopied.get_original_resource_link_id(self.request)
        )

    @view_config(brightspace_copied=True)
    def brightspace_copied_launch(self):
        """
        Respond to a launch of a newly-copied Brightspace assignment.

        For more about Brightspace course copy see the BrightspaceCopied
        predicate's docstring.
        """
        return self.course_copied_launch(
            BrightspaceCopied.get_original_resource_link_id(self.request)
        )

    def course_copied_launch(self, original_resource_link_id):
        """
        Respond to a launch of a newly-copied assignment.

        Find the document_url for the original assignment and make a copy of it
        with the new resource_link_id, then launch the assignment as normal.

        Helper method for the *_copied_launch() methods above.

        :param original_resource_link_id: the resource_link_id of the original
            assignment that this assignment was copied from
        """
        tool_consumer_instance_guid = self.context.lti_params[
            "tool_consumer_instance_guid"
        ]

        document_url = self.assignment_service.get(
            tool_consumer_instance_guid, original_resource_link_id
        ).document_url

        self.assignment_service.upsert(
            document_url, tool_consumer_instance_guid, self.context.resource_link_id
        )

        return self.do_launch(document_url)

    @view_config(url_configured=True, schema=URLConfiguredBasicLTILaunchSchema)
    def url_configured_launch(self):
        """
        Respond to a URL-configured assignment launch.

        URL-configured assignment launch requests have the document URL in the
        ``url`` request parameter. This happens in LMS's that support LTI
        deep linking: the document URL is chosen during assignment creation
        and saved in the LMS, which passes it back to us in each launch request.
        All we have to do is pass the URL to Via.
        """
        return self.do_launch(self.request.parsed_params["url"])

    @view_config(
        authorized_to_configure_assignments=True,
        configured=False,
        renderer="lms:templates/file_picker.html.jinja2",
    )
    def unconfigured_launch(self):
        """
        Respond to an unconfigured assignment launch.

        Unconfigured assignment launch requests don't contain any document URL
        or file ID because the assignment's document hasn't been chosen yet.
        This happens in LMS's that don't support LTI deep linking.
        They go straight from assignment creation to launching the assignment
        without the user having had a chance to choose a document.

        When this happens we show the user our document-selection form instead
        of launching the assignment. The user will choose the document and
        we'll save it in our DB. Subsequent launches of the same assignment
        will then be DB-configured launches rather than unconfigured.
        """
        self.context.get_or_create_course()

        form_fields = {
            param: value
            for param, value in self.context.lti_params.items()
            # Don't send over auth related params. We'll use our own authorization header
            if param
            not in ["oauth_nonce", "oauth_timestamp", "oauth_signature", "id_token"]
        }

        form_fields["authorization"] = BearerTokenSchema(
            self.request
        ).authorization_param(self.request.lti_user)

        self.context.js_config.enable_file_picker_mode(
            form_action=self.request.route_url("configure_assignment"),
            form_fields=form_fields,
        )

        return {}

    # pylint:disable=no-self-use
    @view_config(
        authorized_to_configure_assignments=False,
        configured=False,
        renderer="lms:templates/lti/basic_launch/unconfigured_launch_not_authorized.html.jinja2",
    )
    def unconfigured_launch_not_authorized(self):
        """
        Respond to an unauthorized unconfigured assignment launch.

        This happens when an assignment's document hasn't been chosen yet and
        the assignment is launched by a user who isn't authorized to choose the
        document (for example a learner rather than a teacher). We just show an
        error page.
        """
        return {}

    @view_config(
        authorized_to_configure_assignments=True,
        route_name="configure_assignment",
        schema=ConfigureAssignmentSchema,
    )
    def configure_assignment(self):
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
        extra = {}
        if group_set := self.request.parsed_params.get("group_set"):
            extra["group_set_id"] = group_set

        document_url = self.request.parsed_params["document_url"]

        self.assignment_service.upsert(
            document_url,
            self.context.lti_params["tool_consumer_instance_guid"],
            self.context.resource_link_id,
            extra=extra,
        )
        self.context.js_config.add_document_url(document_url)

        self.sync_lti_data_to_h()
        self.store_lti_data()

        self.context.js_config.maybe_enable_grading()

        # When setting the document it's possible the config might need updating
        # based on the type of assignment since it was initialized
        # with `enable_lti_launch_mode` on __init__
        # We need to clear the cache and `enable_lti_launch_mode` again.
        JSConfig._hypothesis_client.fget.cache_clear()  # pylint: disable=protected-access
        self.context.js_config.enable_lti_launch_mode()

        return {}
