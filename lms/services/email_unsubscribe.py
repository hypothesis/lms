from datetime import timedelta
from functools import partial
from typing import Callable

from sqlalchemy import exists

from lms.models import EmailUnsubscribe
from lms.services.jwt import JWTService
from lms.services.upsert import bulk_upsert


class EmailUnsubscribeService:
    def __init__(self, db, jwt_service: JWTService, secret: str, route_url: Callable):
        self._db = db
        self._jwt_service = jwt_service
        self._secret = secret
        self._route_url = route_url

    def unsubscribe_url(self, email, tag):
        """Generate the url for `email.unsubscribe` with the right token."""
        token = self._generate_token(email, tag)
        return self._route_url("email.unsubscribe", token=token)

    def unsubscribe(self, token):
        """Create a new entry in EmailUnsubscribe based on the email and tag encode in `token`."""
        data = self._decode_token(token)

        bulk_upsert(
            self._db,
            model_class=EmailUnsubscribe,
            values=[data],
            index_elements=["email", "tag"],
            update_columns=["updated"],
        )

    def is_unsubscribed(self, email, tag):
        """Check if `email` is unsubscribed for `tag` type emails."""
        return self._db.scalar(
            exists()
            .where(EmailUnsubscribe.email == email, EmailUnsubscribe.tag == tag)
            .select()
        )

    def _generate_token(self, email, tag):
        return self._jwt_service.encode_with_secret(
            {"email": email, "tag": tag},
            self._secret,
            lifetime=timedelta(days=7),
        )

    def _decode_token(self, token):
        return self._jwt_service.decode_with_secret(token, self._secret)


def factory(_context, request):
    return EmailUnsubscribeService(
        request.db,
        request.find_service(iface=JWTService),
        secret=request.registry.settings["jwt_secret"],
        route_url=partial(
            request.route_url, _app_url=request.registry.settings["web_app_url"]
        ),
    )
