import pytest
import sqlalchemy as sa
from h_matchers import Any

from lms.db import BASE
from lms.models._mixins.public_id import PublicIdMixin
from lms.models.public_id import InvalidPublicId, PublicId
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

    def test_public_id_is_not_generated_when_there_is_no_instance_id(self):
        model = ModelTestHost()
        # Note we aren't flushing, so this should not have a `_public_id`
        # pylint: disable=protected-access
        assert not model._public_id

        assert not model.public_id(Regions.US)

    def test_public_id_eq(self, db_session):
        one = ModelTestHost()
        two = ModelTestHost()
        db_session.add_all([one, two])
        db_session.flush()

        result = (
            db_session.query(ModelTestHost)
            .filter(ModelTestHost.public_id_eq(one.public_id(Regions.US), Regions.US))
            .one_or_none()
        )

        assert result == one

    @pytest.mark.parametrize(
        "wrong_param,wrong_value",
        (("region", Regions.CA), ("app_code", "h"), ("model_code", "other_model")),
    )
    def test_public_id_eq_asserts(self, wrong_param, wrong_value):
        wrong_public_id = PublicId(
            **{
                "region": Regions.US,
                "app_code": "lms",
                "model_code": ModelTestHost.public_id_model_code,
                wrong_param: wrong_value,
            }
        )

        with pytest.raises(InvalidPublicId):
            ModelTestHost.public_id_eq(wrong_public_id, Regions.US)

    @pytest.fixture
    def model(self, db_session):
        model = ModelTestHost()
        db_session.add(model)
        db_session.flush()

        return model
