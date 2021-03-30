import pytest
import sqlalchemy as sa

from lms.db import BASE


class Child(BASE):
    __tablename__ = "child"
    id = sa.Column(sa.Integer, primary_key=True)


class ModelClass(BASE):
    __tablename__ = "model_class"
    id = sa.Column(sa.Integer, primary_key=True)
    column = sa.Column(sa.Integer, sa.ForeignKey("child.id"))
    relationship = sa.orm.relationship("Child")


class TestBase:
    def test_we_can_get_columns(self):
        assert sorted(ModelClass.columns()) == [
            "column",
            "id",
        ]

    def test_we_can_update_from_dict(self, model):
        model.update_from_dict(
            {
                "id": 4321,
                "column": "new_value",
                "relationship": "something",
                "missing": "Another value",
            }
        )

        assert model.id == 1234
        assert model.column == "new_value"

    def test_we_can_specify_keys_to_skip(self, model):
        model.update_from_dict(
            {"id": 4321, "column": "new_value"}, skip_keys={"column"}
        )

        assert model.id == 4321
        assert model.column == "original_value"

    def test_we_fail_to_update_when_skip_keys_is_not_a_set(self):
        with pytest.raises(TypeError):
            ModelClass().update_from_dict({}, skip_keys=["a"])

    def test_repr(self):
        model = ModelClass(id=23, column=46)

        assert repr(model) == "ModelClass(id=23, column=46)"

    def test_repr_is_valid_python(self):
        model = ModelClass(id=23, column=46)

        deserialized_model = eval(repr(model))  # pylint:disable=eval-used

        for attr in (
            "id",
            "column",
        ):
            assert getattr(deserialized_model, attr) == getattr(model, attr)

    @pytest.fixture
    def model(self):
        return ModelClass(id=1234, column="original_value")
