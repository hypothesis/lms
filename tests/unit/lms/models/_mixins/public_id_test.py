import pytest
import sqlalchemy as sa
from h_matchers import Any

from lms.db import BASE
from lms.models._mixins.public_id import PublicIdMixin
from lms.models.region import Regions


class ModelTestHost(PublicIdMixin, BASE):
    __tablename__ = "model_test_host"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    public_id_model_code = "model_test"


class TestPublicIdMixin:
    def test_public_id_column(self, model):
        # pylint: disable=protected-access
        assert model._public_id == Any.string.matching(r"[A-Za-z0-9-_]{22}")

    def test_public_id(self, model):
        public_id = model.public_id(region=Regions.CA)
        assert public_id == Any.string.matching(
            r"ca\.lms\.model_test\.[A-Za-z0-9-_]{22}"
        )

    @pytest.fixture
    def model(self, db_session):
        model = ModelTestHost()
        db_session.add(model)
        db_session.flush()

        return model
