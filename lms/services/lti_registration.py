from lms.models import LTIRegistration


class LTIRegistrationService:
    def __init__(self, db):
        self._db = db

    def get(self, issuer, client_id):
        """
        Get a LTIRegistration based on the uniqueness of issuer + client_id.

        - issuer is provided by the platform (ie the LMS) and is generally a URL identifying the LMS.
        - client_id is also provided by the LMS and it should be unique within the issuer.
        """
        return (
            self._db.query(LTIRegistration)
            .filter_by(issuer=issuer, client_id=client_id)
            .one_or_none()
        )


def factory(_context, request):
    return LTIRegistrationService(db=request.db)
