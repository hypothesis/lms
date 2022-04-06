from typing import Optional

from lms.models import LTIRegistration


class LTIRegistrationService:
    def __init__(self, db):
        self._db = db

    def get(self, issuer: str, client_id: Optional[str] = None):
        """
        Get an LTIRegistration based on issuer and client_id.

        For LMSs that support single tenant we'll have only one (issuer,
        client_id) pair and the OIDC request might not provide the client_id so
        the query will be based on issuer only.

        :param issuer: provided by the platform (ie the LMS) and is generally
            a URL identifying the LMS
        :param client_id: provided by the LMS, should be unique within the
            issuer
        """
        query = self._db.query(LTIRegistration).filter_by(issuer=issuer)

        if client_id:
            query = query.filter_by(client_id=client_id)

        return query.one_or_none()


def factory(_context, request):
    return LTIRegistrationService(db=request.db)
