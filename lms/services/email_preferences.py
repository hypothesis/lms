from datetime import timedelta
from typing import Callable

from lms.models import EmailUnsubscribe
from lms.services.jwt import JWTService
from lms.services.upsert import bulk_upsert


class EmailPreferencesService:
    def __init__(self, db, jwt_service: JWTService, secret: str, route_url: Callable):
        self._db = db
        self._jwt_service = jwt_service
        self._secret = secret
        self._route_url = route_url

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
        request.find_service(iface=JWTService),
        secret=request.registry.settings["jwt_secret"],
        route_url=request.route_url,
    )
