import sqlalchemy as sa
from sqlalchemy.orm import mapped_column

from lms.db import Base
from lms.models._mixins import CreatedUpdatedMixin


class LTIRegistration(CreatedUpdatedMixin, Base):
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
    token_url = mapped_column(sa.UnicodeText, nullable=False)
    """Endpoint to request new oauth tokens to use with LTIA APIs"""

    application_instances = sa.orm.relationship(
        "ApplicationInstance", back_populates="lti_registration"
    )
