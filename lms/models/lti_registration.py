from urllib.parse import urlparse

import sqlalchemy as sa

from lms.db import BASE
from lms.models._mixins import CreatedUpdatedMixin


class LTIRegistration(CreatedUpdatedMixin, BASE):
    """
    LTI1.3 registration details.

    From http://www.imsglobal.org/spec/lti/v1p3/migr:

     - LTI 1.3 separates the registration of the tool (security and configuration) from its actual deployment.

     - A tool registration is identified as a client_id issued by the learning platform (the issuer).
    """

    __tablename__ = "lti_registration"
    __table_args__ = (sa.UniqueConstraint("issuer", "client_id"),)

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    issuer = sa.Column(sa.UnicodeText, nullable=False)
    """Identifier of the platform of this registration"""

    client_id = sa.Column(sa.UnicodeText, nullable=False)
    """Unique identifier of the registration at the issuer"""

    auth_login_url = sa.Column(sa.UnicodeText, nullable=False)
    """URL to redirect the clients in the OIDC flow"""

    key_set_url = sa.Column(sa.UnicodeText, nullable=False)
    """Location of the public keys provied by the issuer for this registration"""
    token_url = sa.Column(sa.UnicodeText, nullable=False)
    """Endpoint to request new oauth tokens to use with LTIA APIs"""

    application_instances = sa.orm.relationship(
        "ApplicationInstance", back_populates="lti_registration"
    )

    @staticmethod
    def urls(issuer, client_id):
        auth_login_url = key_set_url = token_url = None
        issuer_host = urlparse(issuer).netloc

        if issuer == "https://blackboard.com":
            # For blackboard all LTI1.3 apps use the same registration
            auth_login_url = "https://developer.blackboard.com/api/v1/gateway/oidcauth"
            key_set_url = f"https://developer.blackboard.com/api/v1/management/applications/{client_id}/jwks.json"
            token_url = (
                "https://developer.blackboard.com/api/v1/gateway/oauth2/jwttoken"
            )
        elif issuer.endswith(".instructure.com"):
            # Different instructure hosted canvas use the same URLs
            auth_login_url = "https://canvas.instructure.com/api/lti/authorize_redirect"
            key_set_url = "https://canvas.instructure.com/api/lti/security/jwks"
            token_url = "https://canvas.instructure.com/login/oauth2/token"
        elif issuer.endswith(".brightspace.com"):
            # Hosted D2L use the issuer URL as the base
            auth_login_url = (
                urlparse("https://brightspace.com/d2l/lti/authenticate")
                ._replace(netloc=issuer_host)
                .geturl()
            )
            key_set_url = (
                urlparse("https://brightspace.com/d2l/.well-known/jwks")
                ._replace(netloc=issuer_host)
                .geturl()
            )
            token_url = (
                urlparse("https://brightspace.com/core/connect/token")
                ._replace(netloc=issuer_host)
                .geturl()
            )

        elif issuer.endswith(".moodlecloud.com"):
            # Hosted moodle use the issuer URL as the base
            auth_login_url = (
                urlparse("https://moodlecloud.com/mod/lti/auth.php")
                ._replace(netloc=issuer_host)
                .geturl()
            )
            key_set_url = (
                urlparse("https://moodlecloud.com/mod/lti/certs.php")
                ._replace(netloc=issuer_host)
                .geturl()
            )
            token_url = (
                urlparse("https://moodlecloud.com/mod/lti/certs.php")
                ._replace(netloc=issuer_host)
                .geturl()
            )

        return {
            "auth_login_url": auth_login_url,
            "key_set_url": key_set_url,
            "token_url": token_url,
        }
