from unittest.mock import sentinel

import pytest
from h_matchers import Any
from sqlalchemy import select

from lms.models import UserPreferences
from lms.services.user_preferences import UserPreferencesService, factory
from tests import factories


class TestUserPreferencesService:
    def test_get_returns_a_new_UserPreferences_if_none_exists(self, svc):
        assert svc.get("test_h_userid") == Any.object.of_type(
            UserPreferences
        ).with_attrs({"h_userid": "test_h_userid", "preferences": {}})

    def test_get_returns_an_existing_UserPreferences_if_one_exists(self, svc):
        preferences = factories.UserPreferences()

        assert svc.get(preferences.h_userid) is preferences

    def test_set_creates_a_new_UserPreferences_if_none_exists(self, svc, db_session):
        svc.set("test_h_userid", {"foo": "bar"})

        assert db_session.scalars(
            select(UserPreferences).where(UserPreferences.h_userid == "test_h_userid")
        ).one().preferences == {"foo": "bar"}

    @pytest.mark.parametrize(
        "existing_preferences,expected_preferences",
        [
            ({}, {"foo": "bar"}),
            ({"foo": "gar"}, {"foo": "bar"}),
            ({"gar": "har"}, {"gar": "har", "foo": "bar"}),
        ],
    )
    def test_set_updates_an_existing_UserPreferences_if_one_exists(
        self, svc, existing_preferences, expected_preferences
    ):
        preferences = factories.UserPreferences(preferences=existing_preferences)

        svc.set(preferences.h_userid, {"foo": "bar"})

        assert preferences.preferences == expected_preferences

    @pytest.fixture
    def svc(self, db_session):
        return UserPreferencesService(db_session)


class TestFactory:
    def test_it(self, db_session, pyramid_request, UserPreferencesService):
        result = factory(sentinel.context, pyramid_request)

        UserPreferencesService.assert_called_once_with(db_session)
        assert result == UserPreferencesService.return_value

    @pytest.fixture(autouse=True)
    def UserPreferencesService(self, patch):
        return patch("lms.services.user_preferences.UserPreferencesService")
