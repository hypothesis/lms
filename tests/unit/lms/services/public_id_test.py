import pytest

from tests import factories
from lms.validation import ValidationError
from lms.services.public_id import get_by_public_id
from lms.models import Organization


class TestGetByPublicId:
    def test_get_by_public_id(self, pyramid_request, db_session):
        orgs = factories.Organization.create_batch(2)
        # Set the _public_id in the models
        db_session.flush()

        assert (
            get_by_public_id(
                db_session,
                Organization,
                orgs[0].public_id(pyramid_request.region),
                region=pyramid_request.region,
                app="lms",
                type_="org",
            )
            == orgs[0]
        )

    @pytest.mark.parametrize(
        "public_id",
        ("ID", "es.lms.org.ID", "us.h.org.ID", "us.lms.user.ID"),
        ids=["wrong format", "wrong region", "wrong app", "wrong type"],
    )
    def test_get_by_public_id_with_invalid(
        self, public_id, db_session, pyramid_request
    ):
        with pytest.raises(ValidationError):
            get_by_public_id(
                db_session,
                Organization,
                public_id,
                region=pyramid_request.region,
                app="lms",
                type_="org",
            )
