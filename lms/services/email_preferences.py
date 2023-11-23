from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Callable
from urllib.parse import parse_qs, urlparse

from lms.models import EmailUnsubscribe
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError
from lms.services.jwt import JWTService
from lms.services.upsert import bulk_upsert
from lms.services.user_preferences import UserPreferencesService


class UnrecognisedURLError(Exception):
    pass


class InvalidTokenError(Exception):
    pass


@dataclass(frozen=True)
class EmailPrefs:  # pylint:disable=too-many-instance-attributes
    DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

    h_userid: str
    mon: bool = True
    tue: bool = True
    wed: bool = True
    thu: bool = True
    fri: bool = True
    sat: bool = True
    sun: bool = True

    def days(self) -> dict:
        return {key: value for key, value in asdict(self).items() if key in self.DAYS}


class EmailPreferencesService:
    def __init__(  # pylint:disable=too-many-arguments
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
        """Generate the url for `email.unsubscribe` with the right token."""
        token = self._generate_token(h_userid, tag)
        return self._route_url("email.unsubscribe", _query={"token": token})

    def unsubscribe(self, token):
        """Create a new entry in EmailUnsubscribe based on the email and tag encode in `token`."""
        data = self._decode_token(token)

        bulk_upsert(
            self._db,
            model_class=EmailUnsubscribe,
            values=[data],
            index_elements=["h_userid", "tag"],
            update_columns=["updated"],
        )

    def h_userid(self, url: str) -> str:
        """Return the decoded h_userid from the given URL.

        `url` should be a URL generated by one of this service's methods above.

        :raises UnrecognisedURLError: if the given URL does not appear to be
            one generated by this service
        :raises InvalidTokenError: if the URL's authentication token is invalid
            or has expired
        """
        try:
            token = parse_qs(urlparse(url).query)["token"][0]
        except (KeyError, ValueError) as err:
            raise UnrecognisedURLError() from err

        try:
            return self._decode_token(token)["h_userid"]
        except (ExpiredJWTError, InvalidJWTError) as err:
            raise InvalidTokenError() from err

    KEY_PREFIX = "instructor_email_digests.days."

    def get_preferences(self, h_userid) -> EmailPrefs:
        """Return h_userid's email preferences."""
        user_preferences = self._user_preferences_service.get(h_userid)

        return EmailPrefs(
            h_userid=user_preferences.h_userid,
            **{
                key[len(self.KEY_PREFIX) :]: value
                for key, value in user_preferences.preferences.items()
                if key.startswith(self.KEY_PREFIX)
            },
        )

    def set_preferences(self, prefs: EmailPrefs) -> None:
        """Create or update h_userid's email preferences."""
        self._user_preferences_service.set(
            prefs.h_userid,
            {self.KEY_PREFIX + key: value for key, value in prefs.days().items()},
        )

    def _generate_token(self, h_userid, tag):
        return self._jwt_service.encode_with_secret(
            {"h_userid": h_userid, "tag": tag},
            self._secret,
            lifetime=timedelta(days=30),
        )

    def _decode_token(self, token):
        return self._jwt_service.decode_with_secret(token, self._secret)


def factory(_context, request):
    return EmailPreferencesService(
        request.db,
        secret=request.registry.settings["jwt_secret"],
        route_url=request.route_url,
        jwt_service=request.find_service(iface=JWTService),
        user_preferences_service=request.find_service(UserPreferencesService),
    )
