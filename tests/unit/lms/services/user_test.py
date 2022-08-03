from datetime import datetime
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models import User
from lms.services import UserService
from lms.services.user import UserNotFound, factory
from tests import factories


class TestUserService:
    def test_upsert_user(self, service, lti_user, db_session):
        user = service.upsert_user(lti_user)

        saved_user = db_session.query(User).order_by(User.id.desc()).first()
        assert saved_user == Any.instance_of(User).with_attrs(
            {
                "id": Any.int(),
                "application_instance_id": lti_user.application_instance_id,
                "created": Any.instance_of(datetime),
                "updated": Any.instance_of(datetime),
                "user_id": lti_user.user_id,
                "roles": lti_user.roles,
                "h_userid": lti_user.h_user.userid("authority.example.com"),
            }
        )
        assert saved_user == user

    def test_upsert_user_with_an_existing_user(
        self, service, user, lti_user, db_session
    ):
        user = service.upsert_user(lti_user)

        saved_user = db_session.query(User).get(user.id)
        assert saved_user.id == user.id
        assert saved_user.roles == lti_user.roles
        assert user == saved_user

    def test_get(self, user, service):
        db_user = service.get(user.application_instance, user.user_id)

        assert db_user == user

    def test_get_not_found(self, user, service):
        with pytest.raises(UserNotFound):
            service.get(user.application_instance, "some-other-id")

    @pytest.fixture
    def user(self, lti_user, application_instance):
        return factories.User(
            application_instance=application_instance,
            user_id=lti_user.user_id,
            h_userid=lti_user.h_user.userid("authority.example.com"),
            roles="old_roles",
        )

    @pytest.fixture
    def service(self, db_session):
        return UserService(db_session, h_authority="authority.example.com")


class TestFactory:
    def test_it(self, pyramid_request, UserService):
        user_service = factory(sentinel.context, pyramid_request)

        UserService.assert_called_once_with(
            pyramid_request.db, pyramid_request.registry.settings["h_authority"]
        )
        assert user_service == UserService.return_value

    @pytest.fixture(autouse=True)
    def UserService(self, patch):
        return patch("lms.services.user.UserService")
