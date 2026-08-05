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
        message = "Only instructors can reveal annotations"
        raise HTTPForbidden(message)

    assignment_id = int(request.matchdict["assignment_id"])
    assignment_service = request.find_service(name="assignment")
    assignment = assignment_service.get_by_id(assignment_id)

    # Scope the assignment to the caller. get_by_id looks up by raw primary key,
    # so without these checks any instructor could reveal any assignment by id.
    # - Tenant scope: the assignment's course must belong to the caller's
    #   application instance (guards cross-institution reveal).
    # - Membership scope: the caller must be a member of the assignment (guards
    #   an instructor of a different course within the same institution).
    # - Identity scope: the checkpoint in h is keyed by the document's identity
    #   there (assignment.document_uri), not by our internal document_url. If we
    #   haven't resolved one, no checkpoint can have been synced to h, so there
    #   is nothing to reveal.
    if (
        not assignment
        or not assignment.checkpoint_enabled
        or not assignment.document_uri
        or not assignment.course
        or assignment.course.application_instance_id
        != request.lti_user.application_instance_id
        or not assignment_service.is_member(
            assignment,
            request.lti_user.h_user.userid(request.registry.settings["h_authority"]),
        )
    ):
        message = "Assignment or checkpoint not found"
        raise HTTPNotFound(message)

    # Reveal directly in h — h is the source of truth for reveal state.
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
            "document_uri": assignment.document_uri,
        }
        for grouping in reveal_groupings
    ]

    if not checkpoints:
        message = "No groupings found for this assignment"
        raise HTTPNotFound(message)

    results = h_api.reveal_checkpoints(
        checkpoints=checkpoints,
    )

    # Report h's answer
    reveal_date = None
    revealed = False
    if results:
        for result in results:
            if result.get("revealed"):
                revealed = True
                reveal_date = result.get("reveal_date")
                break

    return {"revealed": revealed, "reveal_date": reveal_date}
