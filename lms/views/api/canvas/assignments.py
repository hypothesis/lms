from pyramid.view import view_config, view_defaults

from lms.security import Permissions


@view_defaults(request_method="POST", renderer="json", permission=Permissions.API)
class AssignmentViews:
    def __init__(self, request):
        self.request = request
        self.assignment_service = request.find_service(name="assignment")
        self.application_instance = request.find_service(
            name="application_instance"
        ).get()

    @view_config(
        route_name="assignment.create",
        request_method="POST",
    )
    def create(self):
        assignment = self.assignment_service.set_document_url(
            self.application_instance.tool_consumer_instance_guid,
            self.request.json_body["content"]["url"],
            ext_lti_assignment_id=self.request.json_body.get("ext_lti_assignment_id"),
        )
        return {"ext_lti_assignment_id": assignment.ext_lti_assignment_id}
