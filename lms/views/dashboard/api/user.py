import logging

from pyramid.view import view_config

from lms.js_config_types import APIStudent, APIStudents
from lms.models import RoleScope, RoleType, User
from lms.security import Permissions
from lms.services import UserService
from lms.views.dashboard.pagination import PaginationParametersMixin, get_page

LOG = logging.getLogger(__name__)


class ListUsersSchema(PaginationParametersMixin):
    """Query parameters to fetch a list of users."""


class UserViews:
    def __init__(self, request) -> None:
        self.request = request
        self.user_service: UserService = request.find_service(UserService)

    @view_config(
        route_name="api.dashboard.students",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
        schema=ListUsersSchema,
    )
    def students(self) -> APIStudents:
        students_query = self.user_service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            instructor_h_userid=self.request.user.h_userid
            if self.request.user
            else None,
        )
        students, pagination = get_page(
            self.request, students_query, [User.display_name, User.id]
        )

        return {
            "students": [
                APIStudent(
                    h_userid=s.h_userid, lms_id=s.user_id, display_name=s.display_name
                )
                for s in students
            ],
            "pagination": pagination,
        }
