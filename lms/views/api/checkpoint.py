from datetime import UTC, datetime

from pyramid.view import view_config

from lms.security import Permissions
from lms.services import HAPI


@view_config(
    route_name="api.checkpoint.reveal",
    request_method="POST",
    renderer="json",
    permission=Permissions.API,
)
def reveal_checkpoint(request):
    if not request.lti_user.is_instructor:
        request.response.status_code = 403
        return {"error": "Only instructors can reveal annotations"}

    assignment_id = int(request.matchdict["assignment_id"])
    assignment_service = request.find_service(name="assignment")
    assignment = assignment_service.get_by_id(assignment_id)

    if not assignment or not assignment.checkpoint:
        request.response.status_code = 404
        return {"error": "Assignment or checkpoint not found"}

    if assignment.checkpoint.reveal_date:
        return {"revealed": True, "reveal_date": assignment.checkpoint.reveal_date.replace(tzinfo=UTC).isoformat()}

    # Set the reveal date on the LMS side (source of truth)
    assignment.checkpoint.reveal_date = datetime.utcnow()  # noqa: DTZ003
    reveal_date_iso = assignment.checkpoint.reveal_date.replace(tzinfo=UTC).isoformat()

    # Sync the reveal to h via the existing sync_checkpoints endpoint
    authority = request.registry.settings["h_authority"]
    h_api = request.find_service(HAPI)
    checkpoints = [
        {
            "group_authority_provided_id": grouping.authority_provided_id,
            "document_uri": assignment.document_url,
            "reveal_date": reveal_date_iso,
        }
        for grouping in assignment.groupings.all()
    ]

    if checkpoints:
        h_api.sync_checkpoints(
            authority=authority,
            checkpoints=checkpoints,
        )

    return {"revealed": True, "reveal_date": reveal_date_iso}
