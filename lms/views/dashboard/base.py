from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized

from lms.security import Permissions


def get_request_assignment(request, assignment_service):
    assignment = assignment_service.get_by_id(request.matchdict["assignment_id"])
    if not assignment:
        raise HTTPNotFound()

    if request.has_permission(Permissions.STAFF):
        # STAFF members in our admin pages can access all assignments
        return assignment

    if not assignment_service.is_member(assignment, request.user):
        raise HTTPUnauthorized()

    return assignment


def get_request_organization(request, organization_service):
    public_id = f"us.lms.org.{request.matchdict['public_id']}"
    organization = organization_service.get_by_public_id(public_id)
    if not organization:
        raise HTTPNotFound()

    if request.has_permission(Permissions.STAFF):
        # STAFF members in our admin pages can access all organizations
        return organization

    # We are only using request_organization for admins now.
    # Return 403's now until we have a need and good design for "is_member"
    raise HTTPUnauthorized()


def get_request_course(request, course_service):
    course = course_service.get_by_id(request.matchdict["course_id"])
    if not course:
        raise HTTPNotFound()

    if request.has_permission(Permissions.STAFF):
        # STAFF members in our admin pages can access all courses
        return course

    if not course_service.is_member(course, request.user):
        raise HTTPUnauthorized()

    return course
