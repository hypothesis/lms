from unittest.mock import sentinel

import pytest
import sqlalchemy as sa
from h_matchers import Any

from lms.db import BASE
from lms.models._mixins.public_id import PublicIdMixin


class ModelTestHost(PublicIdMixin, BASE):
    __tablename__ = "model_test_host"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    public_id_model_code = sentinel.public_id_model_code


class TestPublicIdMixin:
    def test_public_id_column(self, db_session, PublicId):
        model = ModelTestHost()
        db_session.add(model)
        db_session.flush()

        # It's not easy to grab the PublicID generator before it's in the
        # mixin, so we'll be a little less isolated and show it meets the
        # expected regex
        assert model._public_id == Any.string.matching(r"[A-Za-z0-9-_]{22}")

    def test_public_id(self, PublicId):
        model = ModelTestHost()

        result = model.public_id(region=sentinel.region)

        PublicId.assert_called_once_with(
            region=sentinel.region,
            model_code=ModelTestHost.public_id_model_code,
            instance_id=model._public_id,
        )
        assert result == PublicId.return_value

    @pytest.fixture(autouse=True)
    def PublicId(self, patch):
        return patch("lms.models._mixins.public_id.PublicId")
