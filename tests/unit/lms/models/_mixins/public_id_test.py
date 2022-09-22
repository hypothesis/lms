import pytest
import sqlalchemy as sa
from h_matchers import Any
from pytest import param

from lms.db import BASE
from lms.models._mixins.public_id import PublicIdMixin
from lms.models.public_id import InvalidPublicId


class ModelTestHost(PublicIdMixin, BASE):
    __tablename__ = "model_test_host"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    public_id_model_code = "model_test"


class TestPublicIdMixin:
    def test_public_id_column(self, model):
        # pylint: disable=protected-access
        assert model._public_id == Any.string.matching(r"[A-Za-z0-9-_]{22}")

    def test_public_id_getter(self, model):
        assert model.public_id == Any.string.matching(
            r"us\.lms\.model_test\.[A-Za-z0-9-_]{22}"
        )

    def test_public_id_is_not_generated_when_there_is_no_instance_id(self):
        model = ModelTestHost()
        # Note we aren't flushing, so this should not have a `_public_id`
        # pylint: disable=protected-access
        assert not model._public_id

        assert not model.public_id

    def test_public_id_comparator(self, model, db_session):
        result = (
            db_session.query(ModelTestHost)
            .filter(ModelTestHost.public_id == model.public_id)
            .one_or_none()
        )

        assert result == model

    @pytest.mark.parametrize(
        "bad_public_id",
        (
            param("XX.lms.model_test_host.HASH", id="wrong region"),
            param("us.XXX.model_test_host.HASH", id="wrong product"),
            param("us.lms.XXX.HASH", id="wrong model code"),
        ),
    )
    def test_public_id_comparator_raises_for_bad_ids(self, db_session, bad_public_id):
        with pytest.raises(InvalidPublicId):
            db_session.query(ModelTestHost).filter(
                ModelTestHost.public_id == bad_public_id
            ).one_or_none()

    @pytest.fixture
    def model(self, db_session):
        model = ModelTestHost()
        db_session.add(model)
        db_session.flush()

        return model
