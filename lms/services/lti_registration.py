from lms.models import LTIRegistration


class LTIRegistrationService:
    def __init__(self, db):
        self._db = db

    def get(self, issuer: str, client_id: str | None = None):
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
        if not issuer:
            return None

        return self._registration_search_query(
            issuer=issuer, client_id=client_id
        ).one_or_none()

    def get_by_id(self, id_) -> LTIRegistration | None:
        return self._registration_search_query(id_=id_).one_or_none()

    def search_registrations(
        self, *, id_=None, issuer=None, client_id=None, limit=100
    ) -> list[LTIRegistration]:
        """Return the registrations that match all of the passed parameters."""

        return (
            self._registration_search_query(id_=id_, issuer=issuer, client_id=client_id)
            .limit(limit)
            .all()
        )

    def _registration_search_query(
        self, *, id_=None, issuer=None, client_id=None
    ) -> LTIRegistration:
        query = self._db.query(LTIRegistration)
        if id_:
            query = query.filter_by(id=id_)

        if issuer:
            query = query.filter_by(issuer=issuer)

        if client_id:
            query = query.filter_by(client_id=client_id)

        return query

    def create_registration(  # noqa: PLR0913
        self,
        issuer: str,
        client_id: str,
        auth_login_url: str,
        key_set_url: str,
        token_url: str,
    ):
        lti_registration = LTIRegistration(
            issuer=issuer,
            client_id=client_id,
            auth_login_url=auth_login_url,
            key_set_url=key_set_url,
            token_url=token_url,
        )
        self._db.add(lti_registration)
        self._db.flush()  # Force the returned registration to have an ID
        return lti_registration


def factory(_context, request):
    return LTIRegistrationService(db=request.db)
