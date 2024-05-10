import pytest
import sqlalchemy as sa
from h_matchers import Any
from pytest import param

from lms.db import Base
from lms.models._mixins.public_id import PublicIdMixin
from lms.models.public_id import InvalidPublicId


class ModelTestHost(PublicIdMixin, Base):
    __tablename__ = "model_test_host"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    public_id_model_code = "model_test"


@pytest.mark.xdist_group("ModelTestHost")
class TestPublicIdMixin:
    def test_public_id_column(self, model):
        assert model._public_id == Any.string.matching(r"[A-Za-z0-9-_]{22}")  # noqa: SLF001

    def test_public_id_getter(self, model):
        assert model.public_id == Any.string.matching(
            r"us\.lms\.model_test\.[A-Za-z0-9-_]{22}"
        )

    def test_public_id_is_not_generated_when_there_is_no_instance_id(self):
        model = ModelTestHost()
        # Note we aren't flushing, so this should not have a `_public_id`
        assert not model._public_id  # noqa: SLF001

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

    @pytest.fixture(autouse=True, scope="class")
    def create_model_test_host_table(self, db_engine):
        ModelTestHost.__table__.drop(db_engine, checkfirst=True)
        ModelTestHost.__table__.create(db_engine)
        yield
        ModelTestHost.__table__.drop(db_engine)

    @pytest.fixture
    def model(self, db_session):
        model = ModelTestHost()
        db_session.add(model)
        db_session.flush()

        return model
