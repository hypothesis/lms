from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Self
from urllib.parse import parse_qs, urlparse

from sqlalchemy import and_, or_, select

from lms.models import (
    LMSCourseMembership,
    LMSUser,
    LTIRole,
    RoleScope,
    RoleType,
    UserPreferences,
)
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.services.jwt import JWTService
from lms.services.user_preferences import UserPreferencesService


class UnrecognisedURLError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


class EmailTypes(StrEnum):
    """Different types of emails sent by the application."""

    INSTRUCTOR_DIGEST = "instructor_digest"
    MENTION = "mention"


@dataclass
class EmailPreferences:
    DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]  # noqa: RUF012

    h_userid: str
    is_instructor: bool
    mention_email_feature_enabled: bool

    mon: bool = True
    tue: bool = True
    wed: bool = True
    thu: bool = True
    fri: bool = True
    sat: bool = True
    sun: bool = True

    mention_email_subscribed: bool = True

    @staticmethod
    def user_preferences_key_for_email_digest_date(datetime_: datetime) -> str:
        return f"instructor_email_digests.days.{EmailPreferences.DAYS[datetime_.weekday()]}"

    def serialize(self) -> dict[str, bool]:
        return {
            "instructor_email_digests.days.mon": self.mon,
            "instructor_email_digests.days.tue": self.tue,
            "instructor_email_digests.days.wed": self.wed,
            "instructor_email_digests.days.thu": self.thu,
            "instructor_email_digests.days.fri": self.fri,
            "instructor_email_digests.days.sat": self.sat,
            "instructor_email_digests.days.sun": self.sun,
            "mention_email.subscribed": self.mention_email_subscribed,
        }

    @classmethod
    def from_user_preferences(
        cls,
        is_instructor: bool,  # noqa: FBT001
        mention_email_feature_enabled: bool,  # noqa: FBT001
        user_preferences: UserPreferences,
    ) -> Self:
        preferences = user_preferences.preferences

        return cls(
            h_userid=user_preferences.h_userid,
            is_instructor=is_instructor,
            mention_email_feature_enabled=mention_email_feature_enabled,
            mon=preferences.get("instructor_email_digests.days.mon", cls.mon),
            tue=preferences.get("instructor_email_digests.days.tue", cls.tue),
            wed=preferences.get("instructor_email_digests.days.wed", cls.wed),
            thu=preferences.get("instructor_email_digests.days.thu", cls.thu),
            fri=preferences.get("instructor_email_digests.days.fri", cls.fri),
            sat=preferences.get("instructor_email_digests.days.sat", cls.sat),
            sun=preferences.get("instructor_email_digests.days.sun", cls.sun),
            mention_email_subscribed=preferences.get(
                "mention_email.subscribed", cls.mention_email_subscribed
            ),
        )


@dataclass(frozen=True)
class TokenPayload:
    """Payload for the token in an email preferences or unsubscribe link."""

    h_userid: str
    tag: str


class EmailPreferencesService:
    def __init__(
        self,
        db,
        secret: str,
        route_url: Callable,
        jwt_service: JWTService,
        user_preferences_service: UserPreferencesService,
    ):
        self._db = db
        self._secret = secret
        self._route_url = route_url
        self._jwt_service = jwt_service
        self._user_preferences_service = user_preferences_service

    def unsubscribe_url(self, h_userid, tag):
        """Return an email unsubscribe URL for the given h_userid.

        The URL will contain a scoped and time-limited authentication token for
        the given h_userid in a query param.
        """
        return self._url("unsubscribe", h_userid, tag)

    def preferences_url(self, h_userid, tag):
        """Return a URL for the email preferences page for the given h_userid.

        The URL will contain a scoped and time-limited authentication token for
        the given h_userid in a query param.
        """
        return self._url("preferences", h_userid, tag)

    def _url(self, route, h_userid, tag):
        return self._route_url(
            f"email.{route}",
            _query={"token": self._encode_token(TokenPayload(h_userid, tag))},
        )

    def unsubscribe(self, h_userid, tag) -> None:
        """Unsubscribe `h_userid` from emails of type `tag`."""
        email_preferences = self.get_preferences(h_userid)
        if tag == EmailTypes.INSTRUCTOR_DIGEST:
            email_preferences.mon = False
            email_preferences.tue = False
            email_preferences.wed = False
            email_preferences.thu = False
            email_preferences.fri = False
            email_preferences.sat = False
            email_preferences.sun = False
        elif tag == EmailTypes.MENTION:
            email_preferences.mention_email_subscribed = False
        else:  # pragma: no cover
            error_message = f"Unrecognized email tag: {tag}"
            raise ValueError(error_message)

        self.set_preferences(email_preferences)

    def decode(self, url: str) -> TokenPayload:
        """Return the decoded token from the given URL.

        `url` should be a URL generated by one of this service's methods above.

        :raises UnrecognisedURLError: if the given URL does not appear to be
            one generated by this service
        :raises InvalidTokenError: if the URL's authentication token is invalid
            or has expired
        """
        try:
            token = parse_qs(urlparse(url).query)["token"][0]
        except (KeyError, ValueError) as err:
            raise UnrecognisedURLError from err

        try:
            return TokenPayload(
                **self._jwt_service.decode_with_secret(token, self._secret)
            )
        except (ExpiredJWTError, InvalidJWTError) as err:
            raise InvalidTokenError from err

    def get_preferences(self, h_userid) -> EmailPreferences:
        """Return h_userid's email preferences."""
        is_instructor = self._is_instructor(h_userid)

        lms_user: LMSUser = self._db.execute(
            select(LMSUser).where(LMSUser.h_userid == h_userid)
        ).scalar_one()

        ai_settings = lms_user.application_instance.settings

        mention_email_feature_enabled = ai_settings.get_setting(
            ai_settings.fields[ai_settings.Settings.HYPOTHESIS_MENTIONS]
        ) and ai_settings.get_setting(
            ai_settings.fields[ai_settings.Settings.HYPOTHESIS_COLLECT_STUDENT_EMAILS]
        )
        return EmailPreferences.from_user_preferences(
            is_instructor=is_instructor,
            mention_email_feature_enabled=mention_email_feature_enabled,
            user_preferences=self._user_preferences_service.get(h_userid),
        )

    def set_preferences(self, email_preferences: EmailPreferences) -> None:
        """Create or update h_userid's email preferences."""
        self._user_preferences_service.set(
            email_preferences.h_userid, email_preferences.serialize()
        )

    def _encode_token(self, payload: TokenPayload):
        return self._jwt_service.encode_with_secret(
            asdict(payload), self._secret, lifetime=timedelta(days=30)
        )

    def _is_instructor(self, h_userid) -> bool:
        """Check if this h_userid is an instructor anywhere in the system."""
        return (
            self._db.execute(
                select(LMSUser.id)
                .join(LMSCourseMembership)
                .join(LTIRole)
                .where(
                    LMSUser.h_userid == h_userid,
                    or_(
                        and_(
                            LTIRole.type == RoleType.INSTRUCTOR,
                            LTIRole.scope == RoleScope.COURSE,
                        ),
                        and_(
                            LTIRole.type == RoleType.ADMIN,
                            LTIRole.scope == RoleScope.SYSTEM,
                        ),
                    ),
                )
            )
        ).scalar() is not None


def factory(_context, request):
    return EmailPreferencesService(
        request.db,
        secret=request.registry.settings["jwt_secret"],
        route_url=request.route_url,
        jwt_service=request.find_service(iface=JWTService),
        user_preferences_service=request.find_service(UserPreferencesService),
    )
