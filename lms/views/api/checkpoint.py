from pyramid.httpexceptions import HTTPForbidden, HTTPNotFound
from pyramid.view import view_config

from lms.models import Grouping
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
        raise HTTPForbidden("Only instructors can reveal annotations")

    assignment_id = int(request.matchdict["assignment_id"])
    assignment_service = request.find_service(name="assignment")
    assignment = assignment_service.get_by_id(assignment_id)

    if not assignment or not assignment.checkpoint_enabled:
        raise HTTPNotFound("Assignment or checkpoint not found")

    # Reveal directly in h — h is the source of truth for reveal state.
    authority = request.registry.settings["h_authority"]
    h_api = request.find_service(HAPI)
    # If the assignment has section/group groupings, only reveal those —
    # not the course group. The course group's checkpoint may be shared
    # with other assignments that use the same URL, so revealing it would
    # affect those assignments too.
    all_groupings = assignment.groupings.all()
    non_course_groupings = [
        group for group in all_groupings if group.type != Grouping.Type.COURSE
    ]
    reveal_groupings = non_course_groupings if non_course_groupings else all_groupings

    checkpoints = [
        {
            "group_authority_provided_id": grouping.authority_provided_id,
            "document_uri": assignment.document_url,
        }
        for grouping in reveal_groupings
    ]

    if not checkpoints:
        raise HTTPNotFound("No groupings found for this assignment")

    results = h_api.reveal_checkpoints(
        authority=authority,
        checkpoints=checkpoints,
    )

    # Return the reveal date from h's response
    reveal_date = None
    if results:
        for result in results:
            if result.get("revealed"):
                reveal_date = result.get("reveal_date")
                break

    return {"revealed": True, "reveal_date": reveal_date}
