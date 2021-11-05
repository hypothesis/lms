from pyramid.httpexceptions import HTTPInternalServerError
from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.validation import APICreateAssignmentSchema


@view_defaults(request_method="POST", renderer="json", permission=Permissions.API)
class AssignmentsAPIViews:
    def __init__(self, request):
        self.request = request
        self.assignment_service = request.find_service(name="assignment")
        self.application_instance = request.find_service(
            name="application_instance"
        ).get_current()

    @view_config(
        route_name="api.assignments.create",
        request_method="POST",
        schema=APICreateAssignmentSchema,
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
            url = params["content"]["file"]["id"]
        elif content_type == "vitalsource":
            book_id = params["content"]["bookID"]
            cfi = params["content"]["cfi"]
            url = f"vitalsource://book/bookID/{book_id}/cfi/{cfi}"
            extra = {"vitalsource": {"bookID": book_id, "cfi": cfi}}
        else:
            raise HTTPInternalServerError("Unhandled content type on assignment")

        if groupset := params.get("groupset"):
            extra["canvas_groupset"] = groupset

        assignment = self.assignment_service.upsert(
            url,
            self.application_instance.tool_consumer_instance_guid,
            resource_link_id=params.get("resource_link_id"),
            ext_lti_assignment_id=params.get("ext_lti_assignment_id"),
            extra=extra,
        )
        return {"ext_lti_assignment_id": assignment.ext_lti_assignment_id}
