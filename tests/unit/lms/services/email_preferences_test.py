from datetime import timedelta
from unittest.mock import sentinel

import pytest

from lms.models import RoleScope, RoleType
from lms.services.email_preferences import (
    EmailPreferences,
    EmailPreferencesService,
    EmailTypes,
    InvalidTokenError,
    TokenPayload,
    UnrecognisedURLError,
    factory,
)
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from tests import factories


class TestEmailPreferences:
    @pytest.mark.parametrize(
        "kwargs,expected_attrs",
        (
            (
                {},
                {
                    "mon": True,
                    "tue": True,
                    "wed": True,
                    "thu": True,
                    "fri": True,
                    "sat": True,
                    "sun": True,
                },
            ),
            (
                {
                    "mon": False,
                    "tue": False,
                    "wed": False,
                    "thu": False,
                    "fri": False,
                    "sat": False,
                    "sun": False,
                },
                {
                    "mon": False,
                    "tue": False,
                    "wed": False,
                    "thu": False,
                    "fri": False,
                    "sat": False,
                    "sun": False,
                },
            ),
        ),
    )
    def test___init__(self, kwargs, expected_attrs):
        prefs = EmailPreferences(
            is_instructor=sentinel.is_instructor,
            h_userid=sentinel.h_userid,
            mention_email_feature_enabled=sentinel.mention_email_feature_enabled,
            mention_email_subscribed=sentinel.mention_email_subscribed,
            **kwargs,
        )

        assert prefs.h_userid == sentinel.h_userid
        assert prefs.mention_email_subscribed == sentinel.mention_email_subscribed
        assert prefs.is_instructor == sentinel.is_instructor
        assert (
            prefs.mention_email_feature_enabled
            == sentinel.mention_email_feature_enabled
        )
        for attr, value in expected_attrs.items():
            assert getattr(prefs, attr) == value


class TestEmailPreferencesService:
    @pytest.mark.parametrize(
        "method,path",
        [
            ("unsubscribe_url", "unsubscribe"),
            ("preferences_url", "preferences"),
        ],
    )
    def test_url(self, svc, jwt_service, method, path):
        jwt_service.encode_with_secret.return_value = "TOKEN"

        url = getattr(svc, method)(sentinel.h_userid, sentinel.tag)

        jwt_service.encode_with_secret.assert_called_once_with(
            {"h_userid": sentinel.h_userid, "tag": sentinel.tag},
            "SECRET",
            lifetime=timedelta(days=30),
        )
        assert url == f"http://example.com/email/{path}?token=TOKEN"

    def test_unsubscribe_digest(self, svc, user_preferences_service, lms_user):
        svc.unsubscribe(lms_user.h_userid, EmailTypes.INSTRUCTOR_DIGEST)

        user_preferences_service.set.assert_called_once_with(
            user_preferences_service.get.return_value.h_userid,
            {
                "instructor_email_digests.days.mon": False,
                "instructor_email_digests.days.tue": False,
                "instructor_email_digests.days.wed": False,
                "instructor_email_digests.days.thu": False,
                "instructor_email_digests.days.fri": False,
                "instructor_email_digests.days.sat": False,
                "instructor_email_digests.days.sun": False,
                "mention_email.subscribed": user_preferences_service.get.return_value.preferences.get.return_value,
            },
        )

    def test_unsubscribe_mentions(self, svc, user_preferences_service, lms_user):
        svc.unsubscribe(lms_user.h_userid, EmailTypes.MENTION)

        preferences = user_preferences_service.get.return_value.preferences
        user_preferences_service.set.assert_called_once_with(
            user_preferences_service.get.return_value.h_userid,
            {
                "instructor_email_digests.days.mon": preferences.get.return_value,
                "instructor_email_digests.days.tue": preferences.get.return_value,
                "instructor_email_digests.days.wed": preferences.get.return_value,
                "instructor_email_digests.days.thu": preferences.get.return_value,
                "instructor_email_digests.days.fri": preferences.get.return_value,
                "instructor_email_digests.days.sat": preferences.get.return_value,
                "instructor_email_digests.days.sun": preferences.get.return_value,
                "mention_email.subscribed": False,
            },
        )

    def test_unsubscribe_mention(self, svc, user_preferences_service, lms_user):
        svc.unsubscribe(lms_user.h_userid, EmailTypes.MENTION)

        user_preferences_service.set.assert_called_once_with(
            user_preferences_service.get.return_value.h_userid,
            {
                "instructor_email_digests.days.mon": user_preferences_service.get.return_value.preferences.get.return_value,
                "instructor_email_digests.days.tue": user_preferences_service.get.return_value.preferences.get.return_value,
                "instructor_email_digests.days.wed": user_preferences_service.get.return_value.preferences.get.return_value,
                "instructor_email_digests.days.thu": user_preferences_service.get.return_value.preferences.get.return_value,
                "instructor_email_digests.days.fri": user_preferences_service.get.return_value.preferences.get.return_value,
                "instructor_email_digests.days.sat": user_preferences_service.get.return_value.preferences.get.return_value,
                "instructor_email_digests.days.sun": user_preferences_service.get.return_value.preferences.get.return_value,
                "mention_email.subscribed": False,
            },
        )

    def test_decode(self, svc, jwt_service):
        jwt_service.decode_with_secret.return_value = {
            "h_userid": sentinel.h_userid,
            "tag": sentinel.tag,
        }

        token_payload = svc.decode("https://example.com?token=test_token")

        jwt_service.decode_with_secret.assert_called_once_with("test_token", "SECRET")
        assert token_payload == TokenPayload(sentinel.h_userid, sentinel.tag)

    @pytest.mark.parametrize(
        "url",
        ["https://example.com?foo=bar", "https://example.com", "http://["],
    )
    def test_decode_if_URL_is_unrecognised_or_invalid(self, svc, url):
        with pytest.raises(UnrecognisedURLError):
            svc.decode(url)

    @pytest.mark.parametrize(
        "exception_class",
        [ExpiredJWTError, InvalidJWTError],
    )
    def test_decode_if_token_is_invalid_or_expired(
        self, svc, jwt_service, exception_class
    ):
        jwt_service.decode_with_secret.side_effect = exception_class

        with pytest.raises(InvalidTokenError):
            svc.decode("https://example.com?token=test_token")

    @pytest.mark.parametrize("is_instructor", [True, False])
    @pytest.mark.parametrize("is_admin", [True, False])
    @pytest.mark.parametrize("mentions_enabled", [True, False])
    @pytest.mark.parametrize("collect_student_emails", [True, False])
    def test_get_preferences(
        self,
        svc,
        user_preferences_service,
        lms_user,
        request,
        is_instructor,
        is_admin,
        mentions_enabled,
        application_instance,
        collect_student_emails,
    ):
        if is_instructor:
            _ = request.getfixturevalue("lms_user_instructor")

        if is_admin:
            _ = request.getfixturevalue("lms_user_admin")

        application_instance.settings.set("hypothesis", "mentions", mentions_enabled)
        application_instance.settings.set(
            "hypothesis", "collect_student_emails", collect_student_emails
        )

        user_preferences_service.get.return_value = factories.UserPreferences(
            h_userid=lms_user.h_userid,
            preferences={
                "instructor_email_digests.days.mon": True,
                "instructor_email_digests.days.tue": False,
            },
        )

        preferences = svc.get_preferences(lms_user.h_userid)

        user_preferences_service.get.assert_called_once_with(lms_user.h_userid)
        assert preferences == EmailPreferences(
            is_instructor=is_instructor or is_admin,
            mention_email_feature_enabled=mentions_enabled and collect_student_emails,
            h_userid=lms_user.h_userid,
            mon=True,
            tue=False,
        )

    def test_set_preferences(self, svc, user_preferences_service, lms_user):
        svc.set_preferences(
            EmailPreferences(
                is_instructor=False,
                mention_email_feature_enabled=False,
                h_userid=lms_user.h_userid,
                tue=True,
                wed=False,
            )
        )

        user_preferences_service.set.assert_called_once_with(
            lms_user.h_userid,
            {
                "instructor_email_digests.days.mon": True,
                "instructor_email_digests.days.tue": True,
                "instructor_email_digests.days.wed": False,
                "instructor_email_digests.days.thu": True,
                "instructor_email_digests.days.fri": True,
                "instructor_email_digests.days.sat": True,
                "instructor_email_digests.days.sun": True,
                "mention_email.subscribed": True,
            },
        )

    @pytest.fixture
    def svc(self, db_session, jwt_service, pyramid_request, user_preferences_service):
        return EmailPreferencesService(
            db_session,
            "SECRET",
            pyramid_request.route_url,
            jwt_service,
            user_preferences_service,
        )

    @pytest.fixture
    def lms_user(self, application_instance):
        lms_user = factories.LMSUser()
        factories.LMSUserApplicationInstance(
            lms_user=lms_user,
            application_instance=application_instance,
        )
        return lms_user

    @pytest.fixture
    def lms_user_instructor(self, lms_user):
        factories.LMSCourseMembership(
            lms_course=factories.LMSCourse(),
            lms_user=lms_user,
            lti_role=factories.LTIRole(
                scope=RoleScope.COURSE, type=RoleType.INSTRUCTOR
            ),
        )

    @pytest.fixture
    def lms_user_admin(self, lms_user):
        factories.LMSCourseMembership(
            lms_course=factories.LMSCourse(),
            lms_user=lms_user,
            lti_role=factories.LTIRole(scope=RoleScope.SYSTEM, type=RoleType.ADMIN),
        )


class TestFactory:
    def test_it(
        self,
        pyramid_request,
        EmailPreferencesService,
        db_session,
        jwt_service,
        user_preferences_service,
    ):
        svc = factory(sentinel.context, pyramid_request)

        EmailPreferencesService.assert_called_once_with(
            db_session,
            secret="test_secret",  # noqa: S106
            route_url=pyramid_request.route_url,
            jwt_service=jwt_service,
            user_preferences_service=user_preferences_service,
        )
        assert svc == EmailPreferencesService.return_value

    @pytest.fixture
    def EmailPreferencesService(self, patch):
        return patch("lms.services.email_preferences.EmailPreferencesService")
