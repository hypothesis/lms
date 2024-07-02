from unittest.mock import sentinel

import pytest

from lms.js_config_types import APIStudent
from lms.models import RoleScope, RoleType, User
from lms.views.dashboard.api.user import UserViews
from tests import factories


class TestUserViews:
    def test_get_students(self, user_service, pyramid_request, views, get_page):
        students = factories.User.create_batch(5)
        get_page.return_value = students, sentinel.pagination

        response = views.students()

        user_service.get_users.assert_called_once_with(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            instructor_h_userid=pyramid_request.user.h_userid,
        )
        get_page.assert_called_once_with(
            pyramid_request,
            user_service.get_users.return_value,
            [User.display_name, User.id],
        )
        assert response == {
            "students": [
                APIStudent(
                    {
                        "h_userid": c.h_userid,
                        "lms_id": c.user_id,
                        "display_name": c.display_name,
                    }
                )
                for c in students
            ],
            "pagination": sentinel.pagination,
        }

    @pytest.fixture
    def views(self, pyramid_request):
        return UserViews(pyramid_request)

    @pytest.fixture
    def get_page(self, patch):
        return patch("lms.views.dashboard.api.user.get_page")
