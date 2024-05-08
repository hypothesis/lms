from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized

from lms.security import Permissions


def get_request_assignment(request, assignment_service):
    assignment = assignment_service.get_by_id(request.matchdict["id_"])
    if not assignment:
        raise HTTPNotFound()

    if request.has_permission(Permissions.STAFF):
        # STAFF members in our admin pages can access all assignments
        return assignment

    if not assignment_service.is_member(assignment, request.user):
        raise HTTPUnauthorized()

    return assignment
