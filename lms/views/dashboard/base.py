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
