from datetime import datetime
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models import User
from lms.services import UserService
from lms.services.user import factory
from tests import factories


class TestUserService:
    def test_it_with_a_new_user(
        self, service, lti_user, db_session, application_instance_service
    ):
        service.store_lti_user(lti_user)

        application_instance_service.get_by_consumer_key.assert_called_once_with(
            lti_user.oauth_consumer_key
        )
        assert db_session.query(User).one() == Any.instance_of(User).with_attrs(
            {
                "id": Any.int(),
                "application_instance": application_instance_service.get_by_consumer_key.return_value,
                "created": Any.instance_of(datetime),
                "updated": Any.instance_of(datetime),
                "user_id": lti_user.user_id,
                "roles": lti_user.roles,
                "h_userid": lti_user.h_user.userid("authority.example.com"),
            }
        )

    def test_it_with_an_existing_user(self, service, user, lti_user, db_session):
        service.store_lti_user(lti_user)

        users = list(db_session.query(User))
        print(users)

        saved_user = db_session.query(User).one()
        assert saved_user.id == user.id
        assert saved_user.roles == lti_user.roles

    @pytest.fixture
    def application_instance(self, application_instance_service):
        return application_instance_service.get_by_consumer_key.return_value

    @pytest.fixture
    def lti_user(self, application_instance):
        return factories.LTIUser(
            oauth_consumer_key=application_instance.consumer_key, roles="new_roles"
        )

    @pytest.fixture
    def user(self, lti_user, application_instance):
        return factories.User(
            application_instance=application_instance,
            user_id=lti_user.user_id,
            h_userid=lti_user.h_user.userid("authority.example.com"),
            roles="old_roles",
        )

    @pytest.fixture
    def service(self, db_session, application_instance_service):
        return UserService(
            h_authority="authority.example.com",
            db_session=db_session,
            application_instance_service=application_instance_service,
        )


class TestFactory:
    def test_it(self, pyramid_request, application_instance_service, UserService):
        user_service = factory(sentinel.context, pyramid_request)

        UserService.assert_called_once_with(
            application_instance_service=application_instance_service,
            db_session=pyramid_request.db,
            h_authority=pyramid_request.registry.settings["h_authority"],
        )
        assert user_service == UserService.return_value

    @pytest.fixture(autouse=True)
    def UserService(self, patch):
        return patch("lms.services.user.UserService")
