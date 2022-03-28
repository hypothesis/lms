from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.view import view_config, view_defaults

from lms.resources.lti_launch import LTILaunchResource
from lms.security import Permissions
from lms.validation import APICreateAssignmentSchema


@view_defaults(request_method="POST", permission=Permissions.API)
class AssignmentsAPIViews:
    def __init__(self, context, request):
        self.request = request
        self.context: LTILaunchResource = context
        self.assignment_service = request.find_service(name="assignment")
        self.application_instance = request.find_service(
            name="application_instance"
        ).get_current()

    @view_config(
        route_name="api.assignments.create",
        renderer="lms:templates/basic_lti_launch/basic_lti_launch.html.jinja2",
        schema=APICreateAssignmentSchema,
    )
    def create(self):
        """
        Create an assignment in the DB.

        Note that at this point the assignment.resource_link_id == None, it will be filled on first launch.
        """
        params = self.request.parsed_params
        extra = {}

        if group_set := self.request.parsed_params.get("group_set"):
            extra["group_set_id"] = group_set

        self.assignment_service.upsert(
            params["document_url"],
            self.application_instance.tool_consumer_instance_guid,
            resource_link_id=params["resource_link_id"],
            extra=extra,
        )
        self.context.js_config.add_document_url(params["document_url"])

        self.context.sync_lti_data_to_h()
        self.context.store_lti_data()

        self.context.js_config.maybe_enable_grading()
        self.context.js_config.enable_lti_launch_mode()

        return {}
