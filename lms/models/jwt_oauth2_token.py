import sqlalchemy as sa

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class JWTOAuth2Token(CreatedUpdatedMixin, Base):
    """
    JWT based OAuth2Token.

    Similar to `models.OAuth2Token` but using the JWT profile required by LTIA
    APIs.

    These tokens are not valid for a particular user but for one tool from the
    point of view of the LMS. In our system that's identified by
    "LTIRegistration".

    Tokens are also valid for one set of scopes only.

    See the spec for the JWT Profile for OAuth 2.0 over:

       https://datatracker.ietf.org/doc/html/rfc7523

    """

    __tablename__ = "jwt_oauth2_token"
    __table_args__ = (sa.UniqueConstraint("lti_registration_id", "scopes"),)

    id = sa.Column(sa.Integer(), autoincrement=True, primary_key=True)

    # The LTIRegistration that this token belongs to foreign key
    lti_registration_id = sa.Column(
        sa.Integer(),
        sa.ForeignKey("lti_registration.id", ondelete="cascade"),
        nullable=False,
    )

    # The LTIRegistration that this token belongs to foreign key
    lti_registration = sa.orm.relationship(
        "LTIRegistration", foreign_keys=[lti_registration_id]
    )

    # Scopes this token is valid for
    scopes = sa.Column(sa.UnicodeText(), nullable=False)

    # The OAuth 2.0 access token, as received from the authorization server.
    access_token = sa.Column(sa.UnicodeText(), nullable=False)

    # Time at which the toke will expire
    expires_at = sa.Column(sa.DateTime, nullable=False)
