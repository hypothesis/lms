"""Database model for persisting OAuth 2 tokens."""
import datetime

import sqlalchemy as sa

from lms.db import BASE


class OAuth2Token(BASE):
    """
    An OAuth 2.0 access token, refresh token and expiry time.

    These are used when this app is acting as an OAuth 2 client and
    communicating with APIs that require OAuth 2 access token authentication,
    for example the Canvas API.
    """

    __tablename__ = "oauth2_token"
    __table_args__ = (sa.UniqueConstraint("user_id", "consumer_key"),)

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    #: The LTI user_id of the LMS user who this access token belongs to.
    user_id = sa.Column(sa.UnicodeText(), nullable=False)

    #: The LTI consumer_key (oauth_consumer_key) of the application instance
    #: that this access token belongs to.
    consumer_key = sa.Column(
        sa.String(),
        sa.ForeignKey("application_instances.consumer_key", ondelete="cascade"),
        nullable=False,
    )

    #: The ApplicationInstance that this access token belongs to.
    application_instance = sa.orm.relationship(
        "ApplicationInstance", back_populates="access_tokens"
    )

    #: The OAuth 2.0 access token, as received from the authorization server.
    access_token = sa.Column(sa.UnicodeText(), nullable=False)

    #: The OAuth 2.0 refresh token, as received from the authorization server.
    #: This will be null if the authorization server didn't provide a refresh
    #: token.
    refresh_token = sa.Column(sa.UnicodeText())

    #: The lifetime in seconds of the access token, as given to us by the
    #: authorization server.
    #: Null if the authorization server didn't provide an expires_in number.
    expires_in = sa.Column(sa.Integer())

    #: The time when we received `access_token` and `expires_in`.
    #:
    #: This is the time when we received the `access_token` and
    #: `expires_in` values above from the authorization server.
    #:
    #: It's needed to compute whether `expires_in` has elapsed and therefore
    #: `access_token` has expired.
    #:
    #: If database rows are updated in place (rather than being deleted and
    #: inserting new rows) then whenever `access_token` and `expires_in`
    #: are updated with new values from the authorization server, `received_at`
    #: should also be updated to the current time.
    received_at = sa.Column(
        sa.DateTime,
        default=datetime.datetime.utcnow,
        server_default=sa.func.now(),
        nullable=False,
    )

    def __str__(self):
        return (
            f"<OAuth2Token user_id:'{self.user_id}' consumer_key:'{self.consumer_key}'>"
        )

    def __repr__(self):
        return f"<lms.models.OAuth2Token user_id:'{self.user_id}' consumer_key:'{self.consumer_key}' access_token:'{self.access_token}' refresh_token:'{self.refresh_token}' expires_in:{self.expires_in}' received_at:'{self.received_at}'>"
