from typing import Optional
from lms.models import LTIRegistration


class LTIRegistrationService:
    def __init__(self, db):
        self._db = db

    def get(self, issuer: str, client_id: Optional[str] = None):
        """
        Get a LTIRegistration based on issuer and client_id.

        - `issuer` is provided by the platform (ie the LMS) and is generally a URL identifying the LMS.
        - `client_id` is also provided by the LMS and it should be unique within the issuer.
        - For LMS that support single tenant we'll have only one (issuer, client_id) pair
          and the OIDC might not provide the client_id so the query will be based on issuer only.
        """
        query = self._db.query(LTIRegistration).filter_by(issuer=issuer)

        if client_id:
            query = query.filter_by(client_id=client_id)

        return query.one_or_none()


def factory(_context, request):
    return LTIRegistrationService(db=request.db)
