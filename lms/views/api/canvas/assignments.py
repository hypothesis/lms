from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.validation import APICanvasCreateAssignment


@view_defaults(request_method="POST", renderer="json", permission=Permissions.API)
class AssignmentsAPIViews:
    def __init__(self, request):
        self.request = request
        self.assignment_service = request.find_service(name="assignment")
        self.application_instance = request.find_service(
            name="application_instance"
        ).get()

    @view_config(
        route_name="canvas_api.assignments.create",
        request_method="POST",
        schema=APICanvasCreateAssignment,
    )
    def create(self):
        """
        Create an assignment in the DB.

        Note that at this point the assignment.resource_link_id == None, it will be filled on first launch.
        """
        params = self.request.parsed_params
        content = params["content"]
        content_type = content["type"]

        url = None
        extra = {}
        if content_type == "url":
            url = content["url"]
        elif content_type == "file":
            url = f"canvas://file/course/{params['course_id']}/file_id/{params['content']['file']['id']}"
            extra = {"canvas_file": params["content"]["file"]}
        else:
            raise ValueError("Unhandled content type on assignment")

        if groupset := params.get("groupset"):
            extra["canvas_groupset"] = groupset

        assignment = self.assignment_service.set_document_url(
            self.application_instance.tool_consumer_instance_guid,
            url,
            ext_lti_assignment_id=self.request.json_body.get("ext_lti_assignment_id"),
            extra=extra,
        )
        return {"ext_lti_assignment_id": assignment.ext_lti_assignment_id}
