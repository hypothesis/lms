"""Database model for persisting OAuth 2 tokens."""

import datetime
from enum import StrEnum, unique

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from lms.db import Base, varchar_enum

__all__ = ["OAuth2Token"]


@unique
class Service(StrEnum):
    """Enum of the different APIs that OAuth tokens may be used for."""

    LMS = "lms"
    """
    The main API of the LMS that a user belongs to.

    This is the API used for resources that are built-in to the LMS.
    """

    CANVAS_STUDIO = "canvas_studio"
    """
    Canvas Studio API.

    See https://tw.instructuremedia.com/api/public/docs/.
    """


class OAuth2Token(Base):
    """
    An OAuth 2.0 access token, refresh token and expiry time.

    These are used when this app is acting as an OAuth 2 client and
    communicating with APIs that require OAuth 2 access token authentication,
    for example the Canvas API.
    """

    __tablename__ = "oauth2_token"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "application_instance_id", "service"),
    )

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)

    #: The LTI user_id of the LMS user who this access token belongs to.
    user_id = sa.Column(sa.UnicodeText(), nullable=False)

    #: The LTI consumer_key (oauth_consumer_key) of the application instance
    #: that this access token belongs to.
    consumer_key = sa.Column(sa.Unicode(), nullable=True)

    #: The ApplicationInstance that this token belongs to foreign key
    application_instance_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("application_instances.id", ondelete="cascade"),
        nullable=False,
    )

    #: The ApplicationInstance that this access token belongs to.
    application_instance = sa.orm.relationship(
        "ApplicationInstance",
        back_populates="access_tokens",
        foreign_keys=[application_instance_id],
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
    received_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.utcnow, server_default=sa.func.now()
    )

    #: The API that this token is used with. In OAuth 2.0 parlance, this
    #: identifies which kind of resource server the token can be passed to.
    service = varchar_enum(Service, default="lms", server_default="lms", nullable=False)
